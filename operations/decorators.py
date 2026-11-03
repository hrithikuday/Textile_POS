from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def admin_required(view_func):
    @wraps(view_func)
    @login_required(login_url="/accounts/login/")
    def wrapped(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.is_staff):
            messages.error(request, "Administrator access is required.")
            return redirect("sales:sales_add")
        return view_func(request, *args, **kwargs)
    return wrapped


def cashier_required(view_func):
    @wraps(view_func)
    @login_required(login_url="/accounts/login/")
    def wrapped(request, *args, **kwargs):
        user = request.user
        if not (
            user.is_superuser
            or user.is_staff
            or user.groups.filter(name="Cashier").exists()
        ):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapped
