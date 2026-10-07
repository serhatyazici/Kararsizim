from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import User


class UserModelTests(TestCase):
    def test_create_user_lowercases_email_and_username(self):
        user = User.objects.create_user("Deneme@Mail.com", "Ali_01", "gizli-parola-123")
        self.assertEqual(user.email, "deneme@mail.com")
        self.assertEqual(user.username, "ali_01")
        self.assertEqual(str(user), "@ali_01")
        self.assertTrue(user.check_password("gizli-parola-123"))

    def test_login_with_email_backend(self):
        User.objects.create_user("a@b.com", "ali", "gizli-parola-123")
        self.assertTrue(self.client.login(username="a@b.com", password="gizli-parola-123"))

    def test_duplicate_username_is_case_insensitive_at_db_level(self):
        User.objects.create_user("a@b.com", "ali", "x")
        with self.assertRaises(IntegrityError), transaction.atomic():
            # save() küçük harfe çevirdiği için bile atlatılsa DB kısıtı yakalar
            User.objects.bulk_create([User(email="c@d.com", username="ALI")])

    def test_username_validation(self):
        for bad in ["ab", "ali veli", "admin", "Ali", "a" * 21]:
            user = User(email="x@y.com", username=bad)
            with self.assertRaises(ValidationError, msg=bad):
                user.full_clean(exclude=["password"])

    def test_create_superuser(self):
        admin = User.objects.create_superuser("root@b.com", "yonetici", "gizli-parola-123")
        self.assertTrue(admin.is_staff and admin.is_superuser)


class HomePageTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "kararsızım")


class AdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("root@b.com", "yonetici", "gizli-parola-123")
        self.client.force_login(self.admin)

    def test_admin_user_pages_render(self):
        for name in ["admin:accounts_user_changelist", "admin:accounts_user_add"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        change_url = reverse("admin:accounts_user_change", args=[self.admin.pk])
        self.assertEqual(self.client.get(change_url).status_code, 200)

    def test_admin_login_with_email(self):
        self.client.logout()
        response = self.client.post(
            reverse("admin:login"),
            {"username": "root@b.com", "password": "gizli-parola-123", "next": "/admin/"},
        )
        self.assertRedirects(response, "/admin/", fetch_redirect_response=False)
