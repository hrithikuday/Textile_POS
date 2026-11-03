from django.contrib import admin

from .models import LedgerEntry, ProductReturn, Supplier

admin.site.register(Supplier)


@admin.register(ProductReturn)
class ProductReturnAdmin(admin.ModelAdmin):
    list_display = ("id", "sale_detail", "quantity", "processed_by", "created_at")
    readonly_fields = ("sale_detail", "quantity", "reason", "processed_by", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("created_at", "entry_type", "description", "amount", "created_by")
    readonly_fields = (
        "entry_type", "amount", "description", "sale", "product_return",
        "created_by", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
