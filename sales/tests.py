import json

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from customers.models import Customer
from operations.models import LedgerEntry, ProductReturn
from products.models import Category, Product
from sales.models import Sale, SaleDetail


class BillingFlowTests(TestCase):
    def setUp(self):
        self.cashier = User.objects.create_user(username="cashier", password="secret")
        self.cashier.groups.add(Group.objects.create(name="Cashier"))
        self.customer = Customer.objects.create(first_name="Test", last_name="Customer")
        self.category = Category.objects.create(
            name="Fabric", description="Textiles", status="ACTIVE")
        self.product = Product.objects.create(
            name="Cotton", description="Cotton fabric", status="ACTIVE",
            category=self.category, price=50, stock_quantity=3)
        self.client.force_login(self.cashier)

    def post_sale(self, quantity=2, payment=110):
        return self.client.post(
            reverse("sales:sales_add"),
            data=json.dumps({
                "customer": self.customer.pk,
                "tax_percentage": 10,
                "amount_payed": payment,
                "products": [{"id": self.product.pk, "quantity": quantity}],
            }),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def test_checkout_deducts_stock_and_records_audited_sale(self):
        response = self.post_sale()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["receipt_url"], reverse(
            "sales:sales_receipt", args=[1]))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 1)
        self.assertEqual(LedgerEntry.objects.get().amount, 110)
        self.assertEqual(LedgerEntry.objects.get().created_by, self.cashier)

    def test_checkout_rejects_insufficient_payment_and_stock(self):
        response = self.post_sale(payment=100)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Payment cannot be less than the bill total.")
        self.assertEqual(self.post_sale(quantity=4).status_code, 400)
        self.assertEqual(self.product.stock_quantity, 3)
        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_checkout_supports_fractional_meter_quantities(self):
        self.product.unit = "meter"
        self.product.stock_quantity = 3
        self.product.save(update_fields=["unit", "stock_quantity"])
        response = self.post_sale(quantity=1.25, payment=68.75)
        self.assertEqual(response.status_code, 200)
        detail = SaleDetail.objects.get()
        self.assertEqual(detail.quantity, 1.25)
        self.assertEqual(detail.total_detail, 62.5)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 1.75)

    def test_checkout_rejects_more_than_two_decimal_quantity_places(self):
        response = self.post_sale(quantity=0.123, payment=7)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Sale.objects.count(), 0)

    def test_cashier_product_search_only_returns_sellable_products(self):
        response = self.client.get(
            reverse("products:get_products"),
            {"term": "Cot"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [self.product.pk])

        self.product.stock_quantity = 0
        self.product.save(update_fields=["stock_quantity"])
        response = self.client.get(
            reverse("products:get_products"),
            {"term": "Cot"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.json(), [])

    def test_unmanaged_account_cannot_access_cashier_portal(self):
        user = User.objects.create_user(username="unassigned", password="secret")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("sales:sales_add")).status_code, 403)
        self.assertEqual(
            self.client.get(reverse("customers:customers_list")).status_code, 403)

    def test_cashier_can_print_own_receipt_but_not_access_admin_reports(self):
        response = self.post_sale()
        receipt = self.client.get(response.json()["receipt_url"])
        self.assertEqual(receipt.status_code, 200)
        self.assertContains(receipt, "Receipt #1")
        self.assertEqual(self.client.get(reverse("operations:reports")).status_code, 302)
        self.assertEqual(self.client.get(reverse("sales:sales_list")).status_code, 302)

    def test_return_restocks_inventory_and_records_tax_inclusive_refund(self):
        admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="secret")
        self.product.stock_quantity = 1
        self.product.save(update_fields=["stock_quantity"])
        sale = Sale.objects.create(
            customer=self.customer, sub_total=100, grand_total=110,
            tax_amount=10, tax_percentage=10, amount_payed=110,
            amount_change=0, created_by=admin)
        detail = SaleDetail.objects.create(
            sale=sale, product=self.product, price=50, quantity=2, total_detail=100)
        self.client.force_login(admin)

        response = self.client.post(reverse("operations:returns"), {
            "sale_detail": detail.pk,
            "quantity": 1,
            "reason": "Size exchange",
        })

        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 2)
        self.assertEqual(ProductReturn.objects.get().refund_amount, 55)
        refund = LedgerEntry.objects.get(entry_type=LedgerEntry.RETURN)
        self.assertEqual(refund.amount, -55)

        self.client.post(reverse("operations:returns"), {
            "sale_detail": detail.pk,
            "quantity": 2,
            "reason": "Over return",
        })
        self.assertEqual(ProductReturn.objects.count(), 1)

    def test_fractional_meter_return_restocks_and_refunds_correctly(self):
        admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="StrongPassword123!")
        self.product.unit = "meter"
        self.product.stock_quantity = 0.75
        self.product.save(update_fields=["unit", "stock_quantity"])
        sale = Sale.objects.create(
            customer=self.customer, sub_total=62.5, grand_total=68.75,
            tax_amount=6.25, tax_percentage=10, amount_payed=68.75,
            amount_change=0, created_by=admin)
        detail = SaleDetail.objects.create(
            sale=sale, product=self.product, price=50, quantity=1.25,
            total_detail=62.5)
        self.client.force_login(admin)

        response = self.client.post(reverse("operations:returns"), {
            "sale_detail": detail.pk,
            "quantity": "0.5",
            "reason": "Cut length exchange",
        })

        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 1.25)
        returned = ProductReturn.objects.get()
        self.assertEqual(returned.quantity, 0.5)
        self.assertEqual(returned.refund_amount, 27.5)
