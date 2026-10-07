import re

from django.http import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import path, reverse

from accounts.models import User

from .models import Option, Poll

PASSWORD = "gizli-parola-123"


def make_poll(author, question="Sinema mı restoran mı?", options=("Sinema", "Restoran")):
    poll = Poll.objects.create(author=author, question=question)
    for position, text in enumerate(options):
        Option.objects.create(poll=poll, text=text, position=position)
    return poll


def h1_count(response):
    return len(re.findall(r"<h1[\s>]", response.content.decode()))


class ErrorPageTests(TestCase):
    def test_custom_404_page(self):
        response = self.client.get("/bu-sayfa-yok/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Ana sayfaya dön", status_code=404)
        self.assertContains(response, "<title>Sayfa bulunamadı — kararsızım</title>", status_code=404, html=True)
        self.assertContains(response, "404", status_code=404)

    def test_missing_poll_uses_custom_404(self):
        response = self.client.get(reverse("polls:detail", args=[9999]))
        self.assertContains(response, "Ana sayfaya dön", status_code=404)

    def test_custom_404_page_for_logged_in_member(self):
        self.client.force_login(User.objects.create_user("a@b.com", "ali", PASSWORD))
        response = self.client.get("/bu-sayfa-yok/")
        self.assertContains(response, "Ana sayfaya dön", status_code=404)
        self.assertContains(response, "@ali", status_code=404)


def failing_view(request):
    raise RuntimeError("Kasıtlı test hatası")


urlpatterns = [path("hata/", failing_view), path("tamam/", lambda request: HttpResponse("ok"))]


@override_settings(ROOT_URLCONF=__name__)
class ServerErrorPageTests(TestCase):
    def test_custom_500_page(self):
        client = Client(raise_request_exception=False)
        response = client.get("/hata/")
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "Bir şeyler ters gitti", status_code=500)
        self.assertContains(response, "Ana sayfaya dön", status_code=500)
        self.assertContains(response, "<title>Bir şeyler ters gitti — kararsızım</title>", status_code=500, html=True)
        # Hatanın teknik ayrıntısı kullanıcıya sızmaz
        self.assertNotContains(response, "Kasıtlı test hatası", status_code=500)


class ShareButtonTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user("yazar@mail.com", "yazar", PASSWORD)
        self.poll = make_poll(self.author, question="Çay mı kahve mi?")

    def test_share_button_on_feed_and_detail_points_to_detail_page(self):
        path_ = reverse("polls:detail", args=[self.poll.pk])
        for url in [reverse("polls:feed"), path_]:
            response = self.client.get(url)
            self.assertContains(response, f'data-share-path="{path_}"')
            self.assertContains(response, 'data-share-title="Çay mı kahve mi?"')
            self.assertContains(response, ">Paylaş</button>")

    def test_share_title_is_escaped(self):
        poll = make_poll(self.author, question='Tırnak " ve <b>etiket</b> sorusu')
        response = self.client.get(reverse("polls:detail", args=[poll.pk]))
        self.assertNotContains(response, "<b>etiket</b>")
        self.assertContains(response, "&quot; ve &lt;b&gt;etiket&lt;/b&gt;")


class FabAndHeaderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ali@mail.com", "ali", PASSWORD)

    def test_visitor_has_no_fab(self):
        self.assertNotContains(self.client.get(reverse("polls:feed")), 'class="fab"')

    def test_member_has_fab_on_feed_but_not_on_create_page(self):
        self.client.force_login(self.user)
        feed = self.client.get(reverse("polls:feed"))
        self.assertContains(feed, 'class="fab"')
        self.assertContains(feed, 'aria-label="Anket oluştur"')
        self.assertNotContains(self.client.get(reverse("polls:create")), 'class="fab"')

    def test_header_create_button_is_hideable_on_mobile(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("polls:feed")), "btn--secondary nav-create")


class ToastTests(TestCase):
    def test_django_messages_are_rendered_as_toasts(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {"email": "yeni@mail.com", "username": "yeni", "password1": PASSWORD, "password2": PASSWORD},
            follow=True,
        )
        self.assertContains(response, 'class="toasts"')
        self.assertContains(response, "data-toast")
        self.assertContains(response, 'class="toast__close"')
        self.assertContains(response, "Hoş geldin @yeni!")
        self.assertNotContains(response, 'class="messages"')

    def test_pages_without_messages_have_no_toast_container(self):
        self.assertNotContains(self.client.get(reverse("polls:feed")), 'class="toasts"')


class PageStructureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ali@mail.com", "ali", PASSWORD)
        self.poll = make_poll(self.user, question="Başlık testi sorusu?")

    def test_page_titles(self):
        self.client.force_login(self.user)
        expected = {
            reverse("polls:feed"): "Anketler — kararsızım",
            reverse("polls:create"): "Anket oluştur — kararsızım",
            reverse("polls:detail", args=[self.poll.pk]): "Başlık testi sorusu? — kararsızım",
        }
        for url, title in expected.items():
            self.assertContains(self.client.get(url), f"<title>{title}</title>", html=True)
        self.client.logout()
        self.assertContains(self.client.get(reverse("accounts:login")), "<title>Giriş — kararsızım</title>", html=True)
        self.assertContains(self.client.get(reverse("accounts:signup")), "<title>Üye ol — kararsızım</title>", html=True)

    def test_skip_link_and_main_landmark(self):
        response = self.client.get(reverse("polls:feed"))
        self.assertContains(response, 'class="skip-link" href="#icerik"')
        self.assertContains(response, 'id="icerik"')

    def test_every_page_has_exactly_one_h1(self):
        urls = [
            reverse("polls:feed"),
            reverse("polls:detail", args=[self.poll.pk]),
            reverse("accounts:login"),
            reverse("accounts:signup"),
        ]
        for url in urls:  # ziyaretçi
            self.assertEqual(h1_count(self.client.get(url)), 1, url)
        self.client.force_login(self.user)
        for url in urls[:2] + [reverse("polls:create")]:  # üye
            self.assertEqual(h1_count(self.client.get(url)), 1, url)

    def test_feed_cards_use_h2_and_detail_uses_h1(self):
        feed = self.client.get(reverse("polls:feed")).content.decode()
        self.assertIn('<h2 class="poll-card__question">', feed)
        detail = self.client.get(reverse("polls:detail", args=[self.poll.pk])).content.decode()
        self.assertIn('<h1 class="poll-card__question">', detail)
        self.assertNotIn('<h2 class="poll-card__question">', detail)

    def test_empty_state_for_members_still_has_single_h1(self):
        Poll.objects.all().delete()
        self.client.force_login(self.user)
        response = self.client.get(reverse("polls:feed"))
        self.assertContains(response, "Henüz anket yok.")
        self.assertEqual(h1_count(response), 1)
