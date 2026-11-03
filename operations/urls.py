from django.urls import path

from . import views

app_name = "operations"
urlpatterns = [
    path("staff/", views.staff_view, name="staff"),
    path("staff/<int:user_id>/toggle/", views.staff_toggle_view, name="staff_toggle"),
    path("suppliers/", views.suppliers_view, name="suppliers"),
    path("suppliers/<int:supplier_id>/edit/", views.supplier_edit_view, name="supplier_edit"),
    path("suppliers/<int:supplier_id>/delete/", views.supplier_delete_view, name="supplier_delete"),
    path("returns/", views.returns_view, name="returns"),
    path("ledger/", views.ledger_view, name="ledger"),
    path("reports/", views.reports_view, name="reports"),
    path("mobile-admin/", views.mobile_admin_view, name="mobile_admin"),
    path("desktop-admin/", views.desktop_admin_view, name="desktop_admin"),
]
