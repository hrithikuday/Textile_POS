from django import forms
from django.contrib.auth.forms import PasswordResetForm


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "placeholder": "Username",
            "class": "form-control form-control-user",
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Password",
            "class": "form-control form-control-user",
        })
    )


class StyledPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email address",
        max_length=254,
        widget=forms.EmailInput(attrs={
            "class": "form-control form-control-user",
            "placeholder": "Enter your account email address",
            "autocomplete": "email",
            "required": True,
        }),
    )
