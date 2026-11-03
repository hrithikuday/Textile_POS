from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.db.models import DecimalField, F, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from decimal import Decimal, InvalidOperation

from products.models import Product
from sales.models import SaleDetail

from .forms import StaffCreationForm, SupplierForm
from .decorators import admin_required
from .models import LedgerEntry, ProductReturn, Supplier


@admin_required
def staff_view(request):
    if request.method == "POST":
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = False
            user.save()
            group, _ = Group.objects.get_or_create(name="Cashier")
            user.groups.add(group)
            messages.success(request, "Staff account created.")
            return redirect("operations:staff")
    else:
        form = StaffCreationForm()
    return render(request, "operations/staff.html", {
        "active_icon": "staff",
        "form": form,
        "staff_members": User.objects.filter(groups__name="Cashier").order_by("username"),
    })


@require_POST
@admin_required
def staff_toggle_view(request, user_id):
    user = get_object_or_404(User, pk=user_id, is_superuser=False, groups__name="Cashier")
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    messages.success(request, "Staff access updated.")
    return redirect("operations:staff")


@admin_required
def suppliers_view(request):
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier added.")
            return redirect("operations:suppliers")
    else:
        form = SupplierForm()
    return render(request, "operations/suppliers.html", {
        "active_icon": "suppliers",
        "form": form,
        "suppliers": Supplier.objects.all(),
    })


@admin_required
def supplier_edit_view(request, supplier_id):
    supplier = get_object_or_404(Supplier, pk=supplier_id)
    form = SupplierForm(request.POST or None, instance=supplier)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Supplier updated.")
        return redirect("operations:suppliers")
    return render(request, "operations/supplier_edit.html", {
        "active_icon": "suppliers",
        "form": form,
        "supplier": supplier,
    })


@require_POST
@admin_required
def supplier_delete_view(request, supplier_id):
    supplier = get_object_or_404(Supplier, pk=supplier_id)
    supplier.delete()
    messages.success(request, "Supplier deleted.")
    return redirect("operations:suppliers")


@admin_required
def returns_view(request):
    if request.method == "POST":
        detail_id = request.POST.get("sale_detail")
        quantity_text = request.POST.get("quantity", "")
        reason = request.POST.get("reason", "").strip()
        try:
            quantity = Decimal(quantity_text)
        except (TypeError, InvalidOperation):
            quantity = Decimal("0")
        if (not detail_id or not quantity.is_finite() or quantity <= 0
                or quantity.as_tuple().exponent < -2 or not reason):
            messages.error(request, "Enter a valid return quantity and reason.")
            return redirect("operations:returns")

        with transaction.atomic():
            detail = get_object_or_404(
                SaleDetail.objects.select_for_update().select_related("product", "sale"),
                pk=detail_id,
            )
            already_returned = sum(item.quantity for item in detail.returns.all())
            available = detail.quantity - already_returned
            if quantity > available:
                messages.error(request, "Return quantity exceeds the unreturned quantity.")
            else:
                product = Product.objects.select_for_update().get(pk=detail.product_id)
                returned = ProductReturn.objects.create(
                    sale_detail=detail,
                    quantity=quantity,
                    reason=reason,
                    processed_by=request.user,
                )
                product.stock_quantity += quantity
                product.save(update_fields=["stock_quantity"])
                LedgerEntry.objects.create(
                    entry_type=LedgerEntry.RETURN,
                    amount=-float(returned.refund_amount),
                    description="Refund for sale #{}".format(detail.sale_id),
                    product_return=returned,
                    created_by=request.user,
                )
                messages.success(request, "Return processed and stock restored.")
        return redirect("operations:returns")

    return_items = SaleDetail.objects.select_related(
        "sale", "product").annotate(
            returned_quantity=Coalesce(
                Sum("returns__quantity"),
                Decimal("0"),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            ),
        ).filter(quantity__gt=F("returned_quantity")).order_by("-sale__date_added")
    return render(request, "operations/returns.html", {
        "active_icon": "returns",
        "sale_details": return_items,
        "returns": ProductReturn.objects.select_related(
            "sale_detail__sale", "sale_detail__product", "processed_by")[:100],
    })


@admin_required
def ledger_view(request):
    entries = LedgerEntry.objects.select_related("created_by", "sale")
    totals = entries.aggregate(
        sales=Coalesce(Sum("amount", filter=Q(entry_type=LedgerEntry.SALE)), 0.0),
        refunds=Coalesce(Sum("amount", filter=Q(entry_type=LedgerEntry.RETURN)), 0.0),
    )
    return render(request, "operations/ledger.html", {
        "active_icon": "ledger",
        "entries": entries[:200],
        "sales_total": totals["sales"],
        "refund_total": totals["refunds"],
        "net_total": totals["sales"] + totals["refunds"],
    })


@admin_required
def reports_view(request):
    sales = LedgerEntry.objects.filter(entry_type=LedgerEntry.SALE)
    returns = LedgerEntry.objects.filter(entry_type=LedgerEntry.RETURN)
    return render(request, "operations/reports.html", {
        "active_icon": "reports",
        "sales_count": sales.count(),
        "sales_total": sales.aggregate(total=Coalesce(Sum("amount"), 0.0))["total"],
        "return_count": returns.count(),
        "refund_total": -returns.aggregate(total=Coalesce(Sum("amount"), 0.0))["total"],
        "product_count": Product.objects.count(),
        "low_stock": Product.objects.filter(stock_quantity__lte=5).select_related("category"),
    })


@admin_required
def mobile_admin_view(request):
    request.session["mobile_admin"] = True
    return redirect("pos:index")


@admin_required
def desktop_admin_view(request):
    request.session["mobile_admin"] = False
    return redirect("pos:index")
