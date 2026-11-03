import json
import os
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.urls import reverse
from django_pos import settings
from products.models import Product
from customers.models import Customer
from operations.decorators import admin_required
from operations.decorators import cashier_required
from operations.models import LedgerEntry

from .models import Sale, SaleDetail


def is_ajax(request):
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"


def can_view_sale(user, sale):
    return user.is_superuser or user.is_staff or sale.created_by_id == user.id


@admin_required
def sales_list_view(request):
    return render(request, "sales/sales.html", {
        "active_icon": "transactions",
        "sales": Sale.objects.select_related("customer", "created_by").order_by("-date_added"),
    })


@cashier_required
def sales_add_view(request):
    context = {
        "active_icon": "billing",
        "customers": [customer.to_select2() for customer in Customer.objects.all()],
    }

    if request.method == "POST" and is_ajax(request):
        try:
            data = json.loads(request.body.decode("utf-8"))
            customer_id = int(data["customer"])
            tax_percentage = Decimal(str(data.get("tax_percentage", 0)))
            amount_payed = Decimal(str(data["amount_payed"]))
            items = data["products"]
            if not isinstance(items, list) or not items:
                raise ValueError("Add at least one product to the bill.")
            if tax_percentage < 0 or tax_percentage > 100 or amount_payed < 0:
                raise ValueError("Enter valid tax and payment amounts.")

            quantities = {}
            for item in items:
                product_id = int(item["id"])
                quantity = Decimal(str(item["quantity"]))
                if quantity <= 0 or quantity.as_tuple().exponent < -2:
                    raise ValueError("Enter a quantity greater than zero with up to 2 decimal places.")
                quantities[product_id] = quantities.get(product_id, 0) + quantity
        except (KeyError, TypeError, ValueError, InvalidOperation, json.JSONDecodeError) as error:
            return JsonResponse({"error": str(error) or "Invalid bill data."}, status=400)

        with transaction.atomic():
            customer = get_object_or_404(Customer, pk=customer_id)
            products = {
                product.pk: product
                for product in Product.objects.select_for_update().filter(
                    pk__in=quantities, status="ACTIVE")
            }
            if len(products) != len(quantities):
                return JsonResponse({"error": "A selected product is no longer available."}, status=400)
            if any(products[product_id].stock_quantity < quantity
                   for product_id, quantity in quantities.items()):
                return JsonResponse({"error": "A selected product has insufficient stock."}, status=400)

            subtotal = sum(
                (Decimal(str(products[product_id].price)) * quantity
                 for product_id, quantity in quantities.items()),
                Decimal("0"),
            )
            tax_amount = (subtotal * tax_percentage / Decimal("100")).quantize(Decimal("0.01"))
            total = (subtotal + tax_amount).quantize(Decimal("0.01"))
            if amount_payed < total:
                return JsonResponse({"error": "Payment cannot be less than the bill total."}, status=400)

            sale = Sale.objects.create(
                customer=customer,
                sub_total=float(subtotal),
                grand_total=float(total),
                tax_amount=float(tax_amount),
                tax_percentage=float(tax_percentage),
                amount_payed=float(amount_payed),
                amount_change=float(amount_payed - total),
                created_by=request.user,
            )
            for product_id, quantity in quantities.items():
                product = products[product_id]
                line_total = Decimal(str(product.price)) * quantity
                SaleDetail.objects.create(
                    sale=sale,
                    product=product,
                    price=product.price,
                    quantity=quantity,
                    total_detail=float(line_total),
                )
                product.stock_quantity -= quantity
                product.save(update_fields=["stock_quantity"])
            LedgerEntry.objects.create(
                entry_type=LedgerEntry.SALE,
                amount=float(total),
                description="Sale #{}".format(sale.pk),
                sale=sale,
                created_by=request.user,
            )

        messages.success(request, "Sale created successfully.")
        return JsonResponse({
            "id": sale.pk,
            "receipt_url": reverse("sales:sales_receipt", args=[sale.pk]),
        })

    if request.method == "POST":
        return JsonResponse({"error": "Use the billing form to submit a sale."}, status=400)
    return render(request, "sales/sales_add.html", context)


@cashier_required
def sales_details_view(request, sale_id):
    sale = get_object_or_404(Sale.objects.select_related("customer"), pk=sale_id)
    if not can_view_sale(request.user, sale):
        raise Http404
    return render(request, "sales/sales_details.html", {
        "active_icon": "transactions",
        "sale": sale,
        "details": SaleDetail.objects.filter(sale=sale).select_related("product"),
    })


@cashier_required
def receipt_pdf_view(request, sale_id):
    sale = get_object_or_404(Sale.objects.select_related("customer"), pk=sale_id)
    if not can_view_sale(request.user, sale):
        raise Http404
    details = SaleDetail.objects.filter(sale=sale).select_related("product")
    template = get_template("sales/sales_receipt_pdf.html")
    html_template = template.render({"sale": sale, "details": details})
    css_url = os.path.join(
        settings.BASE_DIR, "static/css/receipt_pdf/bootstrap.min.css")
    try:
        from weasyprint import CSS, HTML
        pdf = HTML(string=html_template).write_pdf(stylesheets=[CSS(css_url)])
    except (ImportError, OSError):
        return HttpResponse(
            "PDF generation requires WeasyPrint and its native system libraries. "
            "Use the printable receipt page instead.",
            status=503,
            content_type="text/plain",
        )
    return HttpResponse(pdf, content_type="application/pdf")


@cashier_required
def sales_receipt_view(request, sale_id):
    sale = get_object_or_404(Sale.objects.select_related("customer"), pk=sale_id)
    if not can_view_sale(request.user, sale):
        raise Http404
    details = SaleDetail.objects.filter(sale=sale).select_related("product")
    return render(request, "sales/sales_receipt.html", {
        "sale": sale,
        "details": details,
    })
