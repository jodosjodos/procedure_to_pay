import uuid

from django.conf import settings
from django.db import models


class PurchaseRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="purchase_requests", on_delete=models.CASCADE
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="purchase_requests_updated", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    proforma = models.FileField(upload_to="proformas/", blank=True, null=True)
    purchase_order = models.FileField(upload_to="purchase_orders/", blank=True, null=True)
    receipt = models.FileField(upload_to="receipts/", blank=True, null=True)
    document_metadata = models.JSONField(default=dict, blank=True)
    receipt_validation = models.JSONField(default=dict, blank=True)
    last_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="approved_purchase_requests", on_delete=models.SET_NULL, null=True, blank=True
    )
    po_generated_at = models.DateTimeField(null=True, blank=True)

    REQUIRED_APPROVAL_LEVELS = 2

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.title} ({self.status})"

    def can_edit(self, user):
        return user == self.created_by and self.status == self.Status.PENDING


class Approval(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(PurchaseRequest, related_name="approvals", on_delete=models.CASCADE)
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="approvals", on_delete=models.CASCADE)
    approver_level = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("approver_level", "created_at")
        unique_together = ("request", "approver", "approver_level")

    def __str__(self):
        return f"{self.request_id} - L{self.approver_level} ({self.status})"
