from django.contrib import admin

from .models import Approval, PurchaseRequest


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "amount", "created_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "description", "created_by__email")
    readonly_fields = ("created_at", "updated_at", "po_generated_at")


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ("id", "request", "approver", "approver_level", "status", "created_at")
    list_filter = ("approver_level", "status")
    search_fields = ("request__title", "approver__email")
