import json
import os
import re
from typing import Dict, List, Optional

import pdfplumber
from PyPDF2 import PdfReader
from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import Image
import pytesseract

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - openai optional
    OpenAI = None


def _read_pdf_text(path: str) -> str:
    try:
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)


def _read_image_text(path: str) -> str:
    try:
        with Image.open(path) as img:
            return pytesseract.image_to_string(img)
    except Exception:
        return ""


def extract_text(path: str) -> str:
    if path.lower().endswith(".pdf"):
        return _read_pdf_text(path)
    return _read_image_text(path)


def _extract_currency(value: str) -> Optional[float]:
    match = re.search(r"([0-9]+(?:\.[0-9]{2})?)", value.replace(",", ""))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def _maybe_enrich_with_llm(raw_text: str, metadata: Dict) -> Dict:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not OpenAI:
        return metadata

    try:
        client = OpenAI(api_key=api_key)
        prompt = (
            "Extract vendor name, currency, total amount and list of items "
            "with price from the following purchase proforma text. "
            "Respond in JSON with keys vendor, currency, total, items.\n\n"
            f"{raw_text[:4000]}"
        )
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content
        enriched = {}
        try:
            enriched = json.loads(content)
        except Exception:
            pass
        return {**enriched, **metadata}
    except Exception:
        return metadata


def extract_proforma_metadata(file_field) -> Dict:
    path = file_field.path
    text = extract_text(path)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    vendor = next(
        (
            line.split(":")[1].strip()
            for line in lines
            if line.lower().startswith("vendor")
        ),
        None,
    )
    currency = next(
        (
            line.split(":")[1].strip()
            for line in lines
            if line.lower().startswith("currency")
        ),
        "USD",
    )
    total_line = next((line for line in lines if "total" in line.lower()), "")
    total = _extract_currency(total_line) or _extract_currency(
        str(file_field.instance.amount)
    )

    items: List[Dict] = []
    for line in lines:
        if "-" in line and any(char.isdigit() for char in line):
            amount = _extract_currency(line)
            if amount:
                description = line.split("-")[0].strip()
                items.append({"description": description, "price": amount})

    metadata = {
        "vendor": vendor or "Unknown Vendor",
        "currency": currency,
        "total": total,
        "items": items
        or [
            {
                "description": file_field.instance.title,
                "price": float(file_field.instance.amount),
            }
        ],
        "text_preview": text[:500],
    }

    return _maybe_enrich_with_llm(text, metadata)


def generate_purchase_order(purchase_request, metadata: Dict) -> Dict:
    timestamp = timezone.now()
    po_number = f"PO-{timestamp:%Y%m%d}-{str(purchase_request.id)[:8].upper()}"

    items = metadata.get("items") or [
        {
            "description": purchase_request.description,
            "price": float(purchase_request.amount),
        }
    ]
    total = metadata.get("total") or float(purchase_request.amount)

    lines = [
        f"Purchase Order: {po_number}",
        f"Generated: {timestamp.isoformat()}",
        f"Vendor: {metadata.get('vendor', 'Unknown Vendor')}",
        "",
        "Items:",
    ]

    for item in items:
        lines.append(f"- {item.get('description')}: {item.get('price')}")

    lines.append("")
    lines.append(f"Total ({metadata.get('currency', 'USD')}): {total}")

    content = "\n".join(lines)
    file_name = f"{po_number}.txt"
    purchase_request.purchase_order.save(
        file_name, ContentFile(content.encode("utf-8")), save=False
    )
    purchase_request.po_generated_at = timestamp

    po_metadata = {
        "po_number": po_number,
        "generated_at": timestamp.isoformat(),
        "items": items,
        "total": total,
        "currency": metadata.get("currency", "USD"),
    }

    document_metadata = purchase_request.document_metadata or {}
    document_metadata["purchase_order"] = po_metadata
    purchase_request.document_metadata = document_metadata
    return po_metadata


def validate_receipt(purchase_request, receipt_file) -> Dict:
    metadata = purchase_request.document_metadata or {}
    po_data = metadata.get("purchase_order", {})
    text = extract_text(receipt_file.path)
    text_lower = text.lower()

    vendor = po_data.get("vendor") or metadata.get("vendor", "")
    vendor_match = bool(vendor and vendor.lower() in text_lower)

    total = po_data.get("total") or purchase_request.amount
    price_match = bool(total and str(total) in text)

    discrepancies = []
    if not vendor_match:
        discrepancies.append("Vendor name mismatch")
    if not price_match:
        discrepancies.append("Total amount mismatch")

    validation = {
        "is_valid": not discrepancies,
        "discrepancies": discrepancies,
        "vendor_match": vendor_match,
        "price_match": price_match,
        "items_match": bool(po_data.get("items")),
        "checked_at": timezone.now().isoformat(),
    }

    purchase_request.receipt_validation = validation
    return validation
