from django.conf import settings
from django.db import models
from django.utils import timezone
from decimal import Decimal

from products.models import Product
from sales.models import Sale, SaleDetail


class Supplier(models.Model):
    name = models.CharField(max_length=160)
    contact_name = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductReturn(models.Model):
    sale_detail = models.ForeignKey(
        SaleDetail, on_delete=models.PROTECT, related_name="returns")
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=240)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    @property
    def refund_amount(self):
        subtotal = Decimal(str(self.sale_detail.price)) * self.quantity
        tax_multiplier = Decimal("1") + (
            Decimal(str(self.sale_detail.sale.tax_percentage)) / Decimal("100"))
        return (subtotal * tax_multiplier).quantize(Decimal("0.01"))


class LedgerEntry(models.Model):
    SALE = "SALE"
    RETURN = "RETURN"
    ENTRY_TYPES = ((SALE, "Sale"), (RETURN, "Return"))

    entry_type = models.CharField(max_length=12, choices=ENTRY_TYPES)
    amount = models.FloatField()
    description = models.CharField(max_length=240)
    sale = models.ForeignKey(
        Sale, on_delete=models.SET_NULL, null=True, blank=True, related_name="ledger_entries")
    product_return = models.OneToOneField(
        ProductReturn, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ledger_entry")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return "{}: {}".format(self.get_entry_type_display(), self.amount)
