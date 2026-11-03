from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from operations.models import Supplier
from customers.models import Customer
from products.models import Category, Product


class AdminPortalTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="secret")
        self.client.force_login(self.admin)

    def test_mobile_admin_mode_is_available_to_admin_and_persists(self):
        response = self.client.get(reverse("operations:mobile_admin"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session["mobile_admin"])
        self.assertContains(self.client.get(reverse("operations:suppliers")), "Suppliers")

    def test_admin_can_create_staff_account_and_staff_cannot_open_admin_pages(self):
        response = self.client.post(reverse("operations:staff"), {
            "username": "new-cashier",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!",
        })
        self.assertEqual(response.status_code, 302)
        cashier = User.objects.get(username="new-cashier")
        self.assertFalse(cashier.is_staff)
        self.assertTrue(cashier.groups.filter(name="Cashier").exists())

        self.client.force_login(cashier)
        response = self.client.get(reverse("operations:staff"))
        self.assertEqual(response.status_code, 302)

    def test_admin_portal_pages_render(self):
        paths = [
            reverse("pos:index"),
            reverse("products:products_list"),
            reverse("products:categories_list"),
            reverse("customers:customers_list"),
            reverse("sales:sales_list"),
            reverse("operations:staff"),
            reverse("operations:suppliers"),
            reverse("operations:returns"),
            reverse("operations:ledger"),
            reverse("operations:reports"),
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
        add_paths = [
            reverse("products:products_add"),
            reverse("products:categories_add"),
            reverse("customers:customers_add"),
            reverse("sales:sales_add"),
        ]
        for path in add_paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
        response = self.client.get(reverse("operations:mobile_admin"), follow=True)
        self.assertContains(response, 'class="mobile-admin"')
        self.assertContains(response, 'id="mobileSidebarToggle"')
        self.assertContains(response, 'id="mobileSidebarBackdrop"')
        self.assertNotContains(response, 'id="mobileAdminMore"')

    def test_default_textile_categories_are_available(self):
        names = set(Category.objects.values_list("name", flat=True))
        self.assertTrue({
            "Fabrics & Dress Materials",
            "Sarees",
            "Kurtis & Kurtas",
            "Shirts & Tops",
            "Dresses & Gowns",
            "Bottom Wear",
            "Dupattas & Shawls",
            "Kidswear",
            "Home Textiles",
            "Accessories",
        }.issubset(names))
        self.assertTrue(Category.objects.filter(
            name="Sarees", status="ACTIVE").exists())

    def test_admin_can_create_stocked_product_and_supplier(self):
        category = Category.objects.create(
            name="Woven", description="Woven fabrics", status="ACTIVE")
        response = self.client.post(reverse("products:products_add"), {
            "name": "Linen",
            "state": "ACTIVE",
            "description": "Natural linen",
            "material": "Linen",
            "color": "Natural",
            "size": "150cm",
            "unit": "meter",
            "category": category.pk,
            "price": "25.50",
            "stock_quantity": "20.25",
            "sku": "",
        })
        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(name="Linen")
        self.assertEqual(product.stock_quantity, 20.25)
        self.assertEqual(product.material, "Linen")
        self.assertEqual(product.unit, "meter")
        self.assertTrue(product.sku.startswith("TX-"))
        sku = product.sku
        response = self.client.post(
            reverse("products:products_update", args=[product.pk]),
            {
                "name": "Linen",
                "state": "ACTIVE",
                "description": "Natural linen",
                "material": "Linen",
                "color": "Natural",
                "size": "150cm",
                "unit": "meter",
                "category": category.pk,
                "price": "25.50",
                "stock_quantity": "20.25",
                "sku": product.sku,
            },
        )
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.sku, sku)
        self.assertEqual(product.stock_quantity, 20.25)

        response = self.client.post(
            reverse("products:categories_update", args=[category.pk]),
            {"name": "Woven", "state": "ACTIVE", "description": "Woven fabrics"},
        )
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse("operations:suppliers"), {
            "name": "Fabric House",
            "contact_name": "A Supplier",
            "email": "supplier@example.com",
            "phone": "555-0123",
            "address": "Textile market",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Supplier.objects.filter(name="Fabric House").exists())

    def test_staff_can_update_customer_information(self):
        customer = Customer.objects.create(first_name="Ada", last_name="Loom")
        response = self.client.post(
            reverse("customers:customers_update", args=[customer.pk]),
            {
                "first_name": "Ada",
                "last_name": "Weaver",
                "address": "",
                "email": "",
                "phone": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        customer.refresh_from_db()
        self.assertEqual(customer.get_full_name(), "Ada Weaver")
