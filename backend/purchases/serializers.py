from typing import Any, Dict

from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import Approval, PurchaseRequest


class ApprovalSerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(source="approver.name", read_only=True)

    class Meta:
        model = Approval
        fields = (
            "id",
            "approver_id",
            "approver_name",
            "approver_level",
            "status",
            "comment",
            "created_at",
        )
        read_only_fields = fields


class PurchaseRequestSerializer(serializers.ModelSerializer):
    approvals = ApprovalSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source="created_by.name", read_only=True)
    created_by = serializers.IntegerField(source="created_by_id", read_only=True)
    user = UserSerializer(source="created_by", read_only=True)

    class Meta:
        model = PurchaseRequest
        fields = (
            "id",
            "title",
            "description",
            "amount",
            "status",
            "created_by",
            "created_by_name",
            "user",
            "created_at",
            "updated_at",
            "proforma",
            "purchase_order",
            "receipt",
            "document_metadata",
            "receipt_validation",
            "approvals",
        )
        read_only_fields = (
            "id",
            "status",
            "created_by",
            "created_by_name",
            "user",
            "created_at",
            "updated_at",
            "purchase_order",
            "receipt",
            "document_metadata",
            "receipt_validation",
            "approvals",
        )
        extra_kwargs = {
            "proforma": {"write_only": True, "required": False, "allow_null": True},
        }

    def to_representation(self, instance: PurchaseRequest) -> Dict[str, Any]:
        data = super().to_representation(instance)
        request = self.context.get("request")

        def build_url(file_field):
            if not file_field:
                return None
            url = file_field.url
            return request.build_absolute_uri(url) if request else url

        data["proforma"] = build_url(instance.proforma)
        data["purchase_order"] = build_url(instance.purchase_order)
        data["receipt"] = build_url(instance.receipt)
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        proforma = validated_data.pop("proforma", None)
        purchase_request = PurchaseRequest.objects.create(created_by=user, **validated_data)
        if proforma:
            purchase_request.proforma = proforma
            purchase_request.save()
        return purchase_request

    def update(self, instance, validated_data):
        if not instance.can_edit(self.context["request"].user):
            raise serializers.ValidationError("Only pending requests can be updated by their creator.")

        proforma = validated_data.pop("proforma", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if proforma:
            instance.proforma = proforma
        instance.save()
        return instance


class ApprovalActionSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class ReceiptUploadSerializer(serializers.Serializer):
    receipt = serializers.FileField()


