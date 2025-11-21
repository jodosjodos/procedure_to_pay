"""
Comprehensive unit tests for the purchases app.
Tests cover models, views, serializers, and document processing.
"""
import json
import os
import tempfile
from decimal import Decimal
from io import BytesIO
from unittest.mock import MagicMock, Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from .models import Approval, PurchaseRequest
from .services.document_processing import (
    extract_proforma_metadata,
    generate_purchase_order,
    validate_receipt,
)


class PurchaseRequestModelTest(TestCase):
    """Test PurchaseRequest model."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            email="staff@test.com",
            password="testpass123",
            role=User.Roles.STAFF,
            name="Staff User",
        )

    def test_create_purchase_request(self):
        """Test creating a purchase request."""
        request = PurchaseRequest.objects.create(
            title="Test Request",
            description="Test description",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
        )
        self.assertEqual(request.status, PurchaseRequest.Status.PENDING)
        self.assertEqual(request.title, "Test Request")
        self.assertEqual(request.amount, Decimal("1000.00"))
        self.assertEqual(str(request), "Test Request (pending)")

    def test_can_edit_method(self):
        """Test can_edit method."""
        request = PurchaseRequest.objects.create(
            title="Test Request",
            description="Test description",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
        )

        # Creator can edit pending request
        self.assertTrue(request.can_edit(self.staff_user))

        # Other user cannot edit
        other_user = User.objects.create_user(
            email="other@test.com", password="testpass123", role=User.Roles.STAFF
        )
        self.assertFalse(request.can_edit(other_user))

        # Cannot edit approved request
        request.status = PurchaseRequest.Status.APPROVED
        request.save()
        self.assertFalse(request.can_edit(self.staff_user))

    def test_required_approval_levels(self):
        """Test REQUIRED_APPROVAL_LEVELS constant."""
        self.assertEqual(PurchaseRequest.REQUIRED_APPROVAL_LEVELS, 2)


class ApprovalModelTest(TestCase):
    """Test Approval model."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            email="staff@test.com",
            password="testpass123",
            role=User.Roles.STAFF,
        )
        self.approver_l1 = User.objects.create_user(
            email="approver1@test.com",
            password="testpass123",
            role=User.Roles.APPROVER_L1,
        )
        self.request = PurchaseRequest.objects.create(
            title="Test Request",
            description="Test description",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
        )

    def test_create_approval(self):
        """Test creating an approval."""
        approval = Approval.objects.create(
            request=self.request,
            approver=self.approver_l1,
            approver_level=1,
            status=Approval.Status.PENDING,
        )
        self.assertEqual(approval.status, Approval.Status.PENDING)
        self.assertEqual(approval.approver_level, 1)
        self.assertIn("L1", str(approval))

    def test_approval_unique_together(self):
        """Test unique_together constraint."""
        Approval.objects.create(
            request=self.request,
            approver=self.approver_l1,
            approver_level=1,
            status=Approval.Status.APPROVED,
        )

        # Should update existing, not create duplicate
        approval, created = Approval.objects.update_or_create(
            request=self.request,
            approver=self.approver_l1,
            approver_level=1,
            defaults={"status": Approval.Status.REJECTED},
        )
        self.assertFalse(created)
        self.assertEqual(approval.status, Approval.Status.REJECTED)


class PurchaseRequestViewSetTest(TestCase):
    """Test PurchaseRequestViewSet API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            email="staff@test.com",
            password="testpass123",
            role=User.Roles.STAFF,
            name="Staff User",
        )
        self.approver_l1 = User.objects.create_user(
            email="approver1@test.com",
            password="testpass123",
            role=User.Roles.APPROVER_L1,
            name="Approver L1",
        )
        self.approver_l2 = User.objects.create_user(
            email="approver2@test.com",
            password="testpass123",
            role=User.Roles.APPROVER_L2,
            name="Approver L2",
        )
        self.finance_user = User.objects.create_user(
            email="finance@test.com",
            password="testpass123",
            role=User.Roles.FINANCE,
            name="Finance User",
        )

    def test_create_request_as_staff(self):
        """Test staff can create purchase requests."""
        self.client.force_authenticate(user=self.staff_user)
        data = {
            "title": "New Request",
            "description": "Test description",
            "amount": "1500.00",
        }
        response = self.client.post("/api/requests/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PurchaseRequest.objects.count(), 1)
        self.assertEqual(response.data["title"], "New Request")

    def test_staff_can_only_see_own_requests(self):
        """Test staff users only see their own requests."""
        # Create request by staff_user
        request1 = PurchaseRequest.objects.create(
            title="Staff Request",
            description="Test",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
        )

        # Create request by another staff
        other_staff = User.objects.create_user(
            email="other@test.com", password="testpass123", role=User.Roles.STAFF
        )
        request2 = PurchaseRequest.objects.create(
            title="Other Request",
            description="Test",
            amount=Decimal("2000.00"),
            created_by=other_staff,
        )

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/requests/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], str(request1.id))

    def test_approvers_can_see_all_requests(self):
        """Test approvers can see all requests."""
        PurchaseRequest.objects.create(
            title="Request 1",
            description="Test",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
        )
        PurchaseRequest.objects.create(
            title="Request 2",
            description="Test",
            amount=Decimal("2000.00"),
            created_by=self.staff_user,
        )

        self.client.force_authenticate(user=self.approver_l1)
        response = self.client.get("/api/requests/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_approve_request_level_1(self):
        """Test level 1 approver can approve."""
        request = PurchaseRequest.objects.create(
            title="Test Request",
            description="Test",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
        )

        self.client.force_authenticate(user=self.approver_l1)
        response = self.client.patch(
            f"/api/requests/{request.id}/approve/",
            {"comment": "Looks good"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        request.refresh_from_db()
        approval = request.approvals.get(approver=self.approver_l1)
        self.assertEqual(approval.status, Approval.Status.APPROVED)
        self.assertEqual(approval.approver_level, 1)
        # Request should still be pending (needs L2)
        self.assertEqual(request.status, PurchaseRequest.Status.PENDING)

    def test_approve_request_level_2_requires_level_1(self):
        """Test level 2 approver cannot approve without level 1."""
        request = PurchaseRequest.objects.create(
            title="Test Request",
            description="Test",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
        )

        self.client.force_authenticate(user=self.approver_l2)
        response = self.client.patch(
            f"/api/requests/{request.id}/approve/",
            {"comment": "Approved"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Level 1 approval required", str(response.data))

    def test_full_approval_workflow(self):
        """Test complete approval workflow with PO generation."""
        request = PurchaseRequest.objects.create(
            title="Test Request",
            description="Test",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
            document_metadata={"vendor": "Test Vendor", "items": []},
        )

        # Level 1 approval
        self.client.force_authenticate(user=self.approver_l1)
        response = self.client.patch(
            f"/api/requests/{request.id}/approve/",
            {"comment": "L1 approved"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        request.refresh_from_db()
        self.assertEqual(request.status, PurchaseRequest.Status.PENDING)

        # Level 2 approval (should trigger PO generation)
        self.client.force_authenticate(user=self.approver_l2)
        with patch("purchases.services.document_processing.generate_purchase_order") as mock_po:
            mock_po.return_value = {
                "po_number": "PO-20250101-TEST",
                "generated_at": timezone.now().isoformat(),
                "items": [],
                "total": 1000.0,
                "currency": "USD",
            }
            response = self.client.patch(
                f"/api/requests/{request.id}/approve/",
                {"comment": "L2 approved"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_po.assert_called_once()

        request.refresh_from_db()
        self.assertEqual(request.status, PurchaseRequest.Status.APPROVED)
        self.assertIsNotNone(request.purchase_order)

    def test_reject_request(self):
        """Test rejecting a request."""
        request = PurchaseRequest.objects.create(
            title="Test Request",
            description="Test",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
        )

        self.client.force_authenticate(user=self.approver_l1)
        response = self.client.patch(
            f"/api/requests/{request.id}/reject/",
            {"comment": "Not approved"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        request.refresh_from_db()
        self.assertEqual(request.status, PurchaseRequest.Status.REJECTED)
        approval = request.approvals.get(approver=self.approver_l1)
        self.assertEqual(approval.status, Approval.Status.REJECTED)

    def test_cannot_approve_non_pending_request(self):
        """Test cannot approve already approved/rejected request."""
        request = PurchaseRequest.objects.create(
            title="Test Request",
            description="Test",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
            status=PurchaseRequest.Status.APPROVED,
        )

        self.client.force_authenticate(user=self.approver_l1)
        response = self.client.patch(
            f"/api/requests/{request.id}/approve/",
            {"comment": "Approved"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_request_as_staff(self):
        """Test staff can update pending requests."""
        request = PurchaseRequest.objects.create(
            title="Original Title",
            description="Original",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
        )

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.put(
            f"/api/requests/{request.id}/",
            {
                "title": "Updated Title",
                "description": "Updated",
                "amount": "1500.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        request.refresh_from_db()
        self.assertEqual(request.title, "Updated Title")
        self.assertEqual(request.amount, Decimal("1500.00"))

    def test_cannot_update_approved_request(self):
        """Test cannot update approved request."""
        request = PurchaseRequest.objects.create(
            title="Test Request",
            description="Test",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
            status=PurchaseRequest.Status.APPROVED,
        )

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.put(
            f"/api/requests/{request.id}/",
            {
                "title": "Updated Title",
                "description": "Updated",
                "amount": "1500.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_receipt(self):
        """Test submitting receipt for approved request."""
        request = PurchaseRequest.objects.create(
            title="Test Request",
            description="Test",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
            status=PurchaseRequest.Status.APPROVED,
            document_metadata={
                "purchase_order": {
                    "vendor": "Test Vendor",
                    "total": 1000.0,
                }
            },
        )

        receipt_file = SimpleUploadedFile(
            "receipt.pdf", b"fake pdf content", content_type="application/pdf"
        )

        self.client.force_authenticate(user=self.staff_user)
        with patch("purchases.services.document_processing.validate_receipt") as mock_validate:
            mock_validate.return_value = {
                "is_valid": True,
                "discrepancies": [],
                "vendor_match": True,
                "price_match": True,
                "items_match": True,
                "checked_at": timezone.now().isoformat(),
            }
            response = self.client.post(
                f"/api/requests/{request.id}/submit-receipt/",
                {"receipt": receipt_file},
                format="multipart",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_validate.assert_called_once()

        request.refresh_from_db()
        self.assertIsNotNone(request.receipt)

    def test_submit_receipt_only_owner(self):
        """Test only request owner can submit receipt."""
        request = PurchaseRequest.objects.create(
            title="Test Request",
            description="Test",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
            status=PurchaseRequest.Status.APPROVED,
        )

        other_user = User.objects.create_user(
            email="other@test.com", password="testpass123", role=User.Roles.STAFF
        )

        receipt_file = SimpleUploadedFile(
            "receipt.pdf", b"fake pdf content", content_type="application/pdf"
        )

        self.client.force_authenticate(user=other_user)
        response = self.client.post(
            f"/api/requests/{request.id}/submit-receipt/",
            {"receipt": receipt_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_submit_receipt_only_approved(self):
        """Test receipt can only be submitted for approved requests."""
        request = PurchaseRequest.objects.create(
            title="Test Request",
            description="Test",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
            status=PurchaseRequest.Status.PENDING,
        )

        receipt_file = SimpleUploadedFile(
            "receipt.pdf", b"fake pdf content", content_type="application/pdf"
        )

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            f"/api/requests/{request.id}/submit-receipt/",
            {"receipt": receipt_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authentication_required(self):
        """Test authentication is required for all endpoints."""
        response = self.client.get("/api/requests/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DocumentProcessingTest(TestCase):
    """Test document processing functions."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            email="staff@test.com",
            password="testpass123",
            role=User.Roles.STAFF,
        )
        self.request = PurchaseRequest.objects.create(
            title="Test Request",
            description="Test description",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
        )

    @patch("purchases.services.document_processing.extract_text")
    def test_extract_proforma_metadata(self, mock_extract_text):
        """Test proforma metadata extraction."""
        mock_extract_text.return_value = """
        Vendor: Test Vendor Inc
        Currency: USD
        Total: 1000.00
        
        Item 1 - 500.00
        Item 2 - 500.00
        """

        # Create a mock file field
        mock_file = Mock()
        mock_file.path = "/tmp/test.pdf"
        mock_file.instance = self.request

        with patch("purchases.services.document_processing._maybe_enrich_with_llm") as mock_llm:
            mock_llm.return_value = {}
            metadata = extract_proforma_metadata(mock_file)

            self.assertEqual(metadata["vendor"], "Test Vendor Inc")
            self.assertEqual(metadata["currency"], "USD")
            self.assertEqual(metadata["total"], 1000.0)
            self.assertEqual(len(metadata["items"]), 2)

    def test_generate_purchase_order(self):
        """Test purchase order generation."""
        metadata = {
            "vendor": "Test Vendor",
            "currency": "USD",
            "total": 1000.0,
            "items": [
                {"description": "Item 1", "price": 500.0},
                {"description": "Item 2", "price": 500.0},
            ],
        }

        po_metadata = generate_purchase_order(self.request, metadata)

        self.assertIn("po_number", po_metadata)
        self.assertEqual(po_metadata["total"], 1000.0)
        self.assertEqual(po_metadata["currency"], "USD")
        self.assertIsNotNone(self.request.purchase_order)
        self.assertIsNotNone(self.request.po_generated_at)

    @patch("purchases.services.document_processing.extract_text")
    def test_validate_receipt(self, mock_extract_text):
        """Test receipt validation."""
        self.request.document_metadata = {
            "purchase_order": {
                "vendor": "Test Vendor",
                "total": 1000.0,
                "items": [{"description": "Item 1", "price": 1000.0}],
            }
        }
        self.request.save()

        # Receipt with matching vendor and total
        mock_extract_text.return_value = "Test Vendor Receipt Total: 1000.00"

        mock_receipt = Mock()
        mock_receipt.path = "/tmp/receipt.pdf"

        validation = validate_receipt(self.request, mock_receipt)

        self.assertTrue(validation["is_valid"])
        self.assertTrue(validation["vendor_match"])
        self.assertTrue(validation["price_match"])
        self.assertEqual(len(validation["discrepancies"]), 0)

    @patch("purchases.services.document_processing.extract_text")
    def test_validate_receipt_mismatch(self, mock_extract_text):
        """Test receipt validation with mismatches."""
        self.request.document_metadata = {
            "purchase_order": {
                "vendor": "Test Vendor",
                "total": 1000.0,
            }
        }
        self.request.save()

        # Receipt with different vendor and total
        mock_extract_text.return_value = "Different Vendor Receipt Total: 2000.00"

        mock_receipt = Mock()
        mock_receipt.path = "/tmp/receipt.pdf"

        validation = validate_receipt(self.request, mock_receipt)

        self.assertFalse(validation["is_valid"])
        self.assertFalse(validation["vendor_match"])
        self.assertFalse(validation["price_match"])
        self.assertEqual(len(validation["discrepancies"]), 2)

    @patch("purchases.services.document_processing.OpenAI")
    @patch("purchases.services.document_processing.extract_text")
    def test_llm_enrichment(self, mock_extract_text, mock_openai_class):
        """Test LLM enrichment of metadata."""
        mock_extract_text.return_value = "Some proforma text"
        os.environ["OPENAI_API_KEY"] = "test-key"

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content='{"vendor": "LLM Vendor", "currency": "EUR", "total": 2000, "items": []}'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        metadata = {"vendor": "Original Vendor", "total": 1000.0}
        from purchases.services.document_processing import _maybe_enrich_with_llm

        enriched = _maybe_enrich_with_llm("test text", metadata)

        # Should merge LLM data with original
        self.assertIn("vendor", enriched)
        mock_client.chat.completions.create.assert_called_once()


class PurchaseRequestSerializerTest(TestCase):
    """Test PurchaseRequestSerializer."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            email="staff@test.com",
            password="testpass123",
            role=User.Roles.STAFF,
            name="Staff User",
        )
        self.request = PurchaseRequest.objects.create(
            title="Test Request",
            description="Test description",
            amount=Decimal("1000.00"),
            created_by=self.staff_user,
        )

    def test_serializer_includes_approvals(self):
        """Test serializer includes approval history."""
        approver = User.objects.create_user(
            email="approver@test.com",
            password="testpass123",
            role=User.Roles.APPROVER_L1,
        )
        Approval.objects.create(
            request=self.request,
            approver=approver,
            approver_level=1,
            status=Approval.Status.APPROVED,
            comment="Approved",
        )

        from purchases.serializers import PurchaseRequestSerializer
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get("/api/requests/")
        serializer = PurchaseRequestSerializer(
            self.request, context={"request": request}
        )
        data = serializer.data

        self.assertIn("approvals", data)
        self.assertEqual(len(data["approvals"]), 1)
        self.assertEqual(data["approvals"][0]["status"], "approved")

    def test_serializer_read_only_fields(self):
        """Test read-only fields cannot be set."""
        from purchases.serializers import PurchaseRequestSerializer
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get("/api/requests/")
        serializer = PurchaseRequestSerializer(
            self.request, context={"request": request}
        )
        data = serializer.data

        # These should be read-only
        self.assertIn("id", data)
        self.assertIn("status", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
