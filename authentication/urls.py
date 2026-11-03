from django.urls import path
from django.views.generic import RedirectView
from .views import login_view
from django.contrib.auth.views import (
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import reverse_lazy

from .forms import StyledPasswordResetForm

app_name = "authentication"
urlpatterns = [
    path('accounts/login/', login_view, name="login"),
    path(
        "accounts/login/forgot-password.html",
        RedirectView.as_view(pattern_name="authentication:password_reset"),
        name="forgot_password_legacy",
    ),
    path(
        "accounts/password-reset/",
        PasswordResetView.as_view(
            form_class=StyledPasswordResetForm,
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
            success_url=reverse_lazy("authentication:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "accounts/password-reset/done/",
        PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("authentication:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/done/",
        PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path("accounts/logout/", LogoutView.as_view(), name="logout")
]
