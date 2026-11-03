import re
from urllib.parse import urlparse

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse


class PasswordResetTests(TestCase):
    def test_logout_link_uses_post_and_ends_the_session(self):
        user = User.objects.create_superuser(
            username="logout-user",
            email="logout@example.com",
            password="StrongPassword123!",
        )
        self.client.force_login(user)
        response = self.client.get(reverse("pos:index"))
        self.assertContains(response, 'method="post" action="/accounts/logout/"')

        response = self.client.post(reverse("authentication:logout"))

        self.assertRedirects(response, reverse("authentication:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_flow_sends_link_and_changes_password(self):
        user = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="OriginalPassword123!",
        )
        response = self.client.get(reverse("authentication:login"))
        self.assertContains(response, reverse("authentication:password_reset"))

        response = self.client.post(
            reverse("authentication:password_reset"),
            {"email": user.email},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Check your email")
        self.assertEqual(len(mail.outbox), 1)

        reset_url = re.search(r"https?://\S+", mail.outbox[0].body).group()
        reset_path = urlparse(reset_url).path
        response = self.client.get(reset_path)
        self.assertEqual(response.status_code, 302)
        confirm_path = response["Location"]
        response = self.client.post(confirm_path, {
            "new_password1": "NewStrongPassword456!",
            "new_password2": "NewStrongPassword456!",
        })

        self.assertRedirects(
            response,
            reverse("authentication:password_reset_complete"),
        )
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewStrongPassword456!"))

    def test_legacy_forgot_password_url_redirects_to_reset_form(self):
        response = self.client.get(reverse("authentication:forgot_password_legacy"))
        self.assertRedirects(
            response,
            reverse("authentication:password_reset"),
        )
        self.assertEqual(
            self.client.get(reverse("authentication:password_reset")).status_code,
            200,
        )
