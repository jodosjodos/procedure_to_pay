from django.db import transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from .models import Approval, PurchaseRequest
from .serializers import (
    ApprovalActionSerializer,
    PurchaseRequestSerializer,
    ReceiptUploadSerializer,
)
from .services.document_processing import extract_proforma_metadata, generate_purchase_order, validate_receipt


class PurchaseRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PurchaseRequestSerializer
    queryset = PurchaseRequest.objects.select_related("created_by").prefetch_related("approvals", "approvals__approver")

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == User.Roles.STAFF:
            return qs.filter(created_by=user)
        return qs

    def perform_create(self, serializer):
        purchase_request = serializer.save()
        if purchase_request.proforma:
            metadata = extract_proforma_metadata(purchase_request.proforma)
            purchase_request.document_metadata = {**(purchase_request.document_metadata or {}), **metadata}
            purchase_request.save()

    def perform_update(self, serializer):
        purchase_request = serializer.save()
        if purchase_request.proforma:
            metadata = extract_proforma_metadata(purchase_request.proforma)
            purchase_request.document_metadata = {**(purchase_request.document_metadata or {}), **metadata}
            purchase_request.save()

    @action(detail=True, methods=["patch"], url_path="approve")
    def approve(self, request, pk=None):
        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purchase_request = self.get_object()
        user = request.user
        level = self._get_approver_level(user)

        with transaction.atomic():
            self._ensure_can_approve(purchase_request, level)

            approval, _ = Approval.objects.update_or_create(
                request=purchase_request,
                approver=user,
                approver_level=level,
                defaults={
                    "status": Approval.Status.APPROVED,
                    "comment": serializer.validated_data.get("comment", ""),
                },
            )
            purchase_request.last_approved_by = user

            if self._all_levels_approved(purchase_request):
                purchase_request.status = PurchaseRequest.Status.APPROVED
                metadata = purchase_request.document_metadata or {}
                po_metadata = generate_purchase_order(purchase_request, metadata)
                metadata["purchase_order"] = po_metadata
                purchase_request.document_metadata = metadata

            purchase_request.save()

        return Response(PurchaseRequestSerializer(purchase_request, context={"request": request}).data)

    @action(detail=True, methods=["patch"], url_path="reject")
    def reject(self, request, pk=None):
        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purchase_request = self.get_object()
        user = request.user
        level = self._get_approver_level(user)

        with transaction.atomic():
            self._ensure_can_approve(purchase_request, level)

            Approval.objects.update_or_create(
                request=purchase_request,
                approver=user,
                approver_level=level,
                defaults={
                    "status": Approval.Status.REJECTED,
                    "comment": serializer.validated_data.get("comment", ""),
                },
            )
            purchase_request.status = PurchaseRequest.Status.REJECTED
            purchase_request.save()

        return Response(PurchaseRequestSerializer(purchase_request, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="submit-receipt")
    def submit_receipt(self, request, pk=None):
        purchase_request = self.get_object()
        if request.user != purchase_request.created_by:
            raise PermissionDenied("Only the request owner can submit receipts.")
        if purchase_request.status != PurchaseRequest.Status.APPROVED:
            raise ValidationError("Receipts can only be submitted for approved requests.")
        if purchase_request.receipt:
            raise ValidationError("Receipt already submitted.")

        serializer = ReceiptUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purchase_request.receipt = serializer.validated_data["receipt"]
        validation = validate_receipt(purchase_request, purchase_request.receipt)
        purchase_request.receipt_validation = validation
        purchase_request.save()
        return Response(PurchaseRequestSerializer(purchase_request, context={"request": request}).data)

    def _get_approver_level(self, user: User) -> int:
        if user.role == User.Roles.APPROVER_L1:
            return 1
        if user.role == User.Roles.APPROVER_L2:
            return 2
        raise PermissionDenied("Only approvers can perform this action.")

    def _ensure_can_approve(self, purchase_request: PurchaseRequest, level: int):
        if purchase_request.status != PurchaseRequest.Status.PENDING:
            raise ValidationError("Only pending requests can be acted upon.")
        if level == 2:
            has_level_one = purchase_request.approvals.filter(
                approver_level=1, status=Approval.Status.APPROVED
            ).exists()
            if not has_level_one:
                raise ValidationError("Level 1 approval required before level 2 approvers can act.")

    def _all_levels_approved(self, purchase_request: PurchaseRequest) -> bool:
        approved_levels = set(
            purchase_request.approvals.filter(status=Approval.Status.APPROVED).values_list("approver_level", flat=True)
        )
        return len(approved_levels) >= purchase_request.REQUIRED_APPROVAL_LEVELS
