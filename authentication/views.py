from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render

from .forms import LoginForm


def login_view(request):
    form = LoginForm(request.POST or None)
    message = None

    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user is not None:
            login(request, user)
            if user.is_superuser or user.is_staff:
                return redirect("pos:index")
            return redirect("sales:sales_add")
        message = "Invalid username or password."

    return render(request, "accounts/login.html", {"form": form, "msg": message})
