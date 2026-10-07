from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import include, path, reverse

from .decorators import login_required_with_message
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
        response = self.client.get(reverse("polls:feed"))
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


PASSWORD = "gizli-parola-123"


def signup_data(**overrides):
    data = {
        "email": "yeni@mail.com",
        "username": "yeni_kisi",
        "password1": PASSWORD,
        "password2": PASSWORD,
    }
    data.update(overrides)
    return data


class SignupTests(TestCase):
    def test_signup_page_loads(self):
        self.assertEqual(self.client.get(reverse("accounts:signup")).status_code, 200)

    def test_successful_signup_logs_user_in_and_shows_welcome(self):
        response = self.client.post(reverse("accounts:signup"), signup_data(), follow=True)
        self.assertRedirects(response, "/")
        user = User.objects.get(email="yeni@mail.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertContains(response, "Hoş geldin @yeni_kisi!")
        self.assertContains(response, "@yeni_kisi")

    def test_signup_normalizes_case(self):
        self.client.post(reverse("accounts:signup"), signup_data(email="Yeni@Mail.COM", username="Yeni_Kisi"))
        user = User.objects.get()
        self.assertEqual((user.email, user.username), ("yeni@mail.com", "yeni_kisi"))

    def test_signup_respects_next(self):
        response = self.client.post(reverse("accounts:signup") + "?next=/anket/yeni/", signup_data())
        self.assertRedirects(response, "/anket/yeni/", fetch_redirect_response=False)

    def test_signup_ignores_unsafe_next(self):
        response = self.client.post(
            reverse("accounts:signup") + "?next=https://kotu-site.example/", signup_data()
        )
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user("Deneme@Mail.com", "baska", PASSWORD)
        response = self.client.post(reverse("accounts:signup"), signup_data(email="deneme@mail.com"))
        self.assertContains(response, "Bu e-posta adresiyle zaten bir hesap var.")
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_username_is_rejected_case_insensitively(self):
        User.objects.create_user("a@b.com", "ali", PASSWORD)
        response = self.client.post(reverse("accounts:signup"), signup_data(username="Ali"))
        self.assertContains(response, "Bu kullanıcı adı zaten alınmış.")
        self.assertEqual(User.objects.count(), 1)

    def test_invalid_usernames_are_rejected_with_turkish_messages(self):
        for bad in ["ab", "ali veli", "admin", "çağrı", "a" * 21]:
            response = self.client.post(reverse("accounts:signup"), signup_data(username=bad))
            self.assertEqual(User.objects.count(), 0, bad)
            self.assertTrue(response.context["form"].errors["username"], bad)
        response = self.client.post(reverse("accounts:signup"), signup_data(username="ab"))
        self.assertContains(response, "3–20 karakter olmalı")
        response = self.client.post(reverse("accounts:signup"), signup_data(username="admin"))
        self.assertContains(response, "Bu kullanıcı adı kullanılamaz.")

    def test_password_mismatch_and_weak_password(self):
        response = self.client.post(reverse("accounts:signup"), signup_data(password2="baska-parola-456"))
        self.assertTrue(response.context["form"].errors["password2"])
        response = self.client.post(
            reverse("accounts:signup"), signup_data(password1="12345678", password2="12345678")
        )
        self.assertTrue(response.context["form"].errors["password2"])
        self.assertEqual(User.objects.count(), 0)

    def test_authenticated_user_is_redirected_away_from_signup(self):
        self.client.force_login(User.objects.create_user("a@b.com", "ali", PASSWORD))
        response = self.client.get(reverse("accounts:signup"))
        self.assertRedirects(response, "/", fetch_redirect_response=False)


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ali@mail.com", "ali", PASSWORD)

    def test_login_with_email_and_password(self):
        response = self.client.post(
            reverse("accounts:login"), {"username": "ALI@mail.com", "password": PASSWORD}
        )
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_respects_next(self):
        response = self.client.post(
            reverse("accounts:login") + "?next=/anket/yeni/",
            {"username": "ali@mail.com", "password": PASSWORD, "next": "/anket/yeni/"},
        )
        self.assertRedirects(response, "/anket/yeni/", fetch_redirect_response=False)

    def test_wrong_password_and_unknown_email_give_same_generic_message(self):
        for email, password in [("ali@mail.com", "yanlis"), ("yok@mail.com", PASSWORD)]:
            response = self.client.post(reverse("accounts:login"), {"username": email, "password": password})
            self.assertContains(response, "E-posta veya parola hatalı.")
            self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)


@login_required_with_message
def protected_view(request):
    return HttpResponse("gizli")


urlpatterns = [
    path("korumali/", protected_view),
    path("", include("accounts.urls")),
]


@override_settings(ROOT_URLCONF=__name__)
class LoginRequiredWithMessageTests(TestCase):
    def test_visitor_is_sent_to_login_with_info_message(self):
        response = self.client.get("/korumali/", follow=True)
        self.assertRedirects(response, "/giris/?next=/korumali/")
        self.assertContains(response, "Anket oluşturmak için giriş yap ya da hemen üye ol.")
        # Giriş sayfasındaki "Üye ol" bağlantısı next değerini taşır
        self.assertContains(response, "/kayit/?next=/korumali/")

    def test_member_passes_through(self):
        self.client.force_login(User.objects.create_user("a@b.com", "ali", PASSWORD))
        self.assertContains(self.client.get("/korumali/"), "gizli")


class PrivacyTests(TestCase):
    def test_no_email_appears_in_any_page(self):
        other = User.objects.create_user("baskasi@gizli.com", "baskasi", PASSWORD)
        me = User.objects.create_user("ben@gizli.com", "ben", PASSWORD)
        self.client.force_login(me)
        for url in ["/", reverse("accounts:login"), reverse("accounts:signup")]:
            html = self.client.get(url, follow=True).content.decode()
            self.assertNotIn(other.email, html, url)
            self.assertNotIn(me.email, html, url)
        self.assertIn("@ben", self.client.get("/").content.decode())
