from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .models import Option, Poll
from .templatetags.poll_extras import avatar_color, time_ago

PASSWORD = "gizli-parola-123"


def make_poll(author, question="Sinema mı restoran mı?", options=("Sinema", "Restoran"), description=""):
    poll = Poll.objects.create(author=author, question=question, description=description)
    Option.objects.bulk_create(
        [Option(poll=poll, text=text, position=i) for i, text in enumerate(options)]
    )
    return poll


def poll_data(**overrides):
    data = {
        "question": "Bu akşam ne yapsam?",
        "description": "",
        "options": ["Sinema", "Restoran"],
    }
    data.update(overrides)
    return data


class PollCreateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ali@mail.com", "ali", PASSWORD)
        self.url = reverse("polls:create")

    def test_visitor_is_redirected_to_login_with_message(self):
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, "/giris/?next=/anket/yeni/")
        self.assertContains(response, "Anket oluşturmak için giriş yap ya da hemen üye ol.")

    def test_visitor_cannot_post(self):
        response = self.client.post(self.url, poll_data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Poll.objects.count(), 0)

    def test_create_page_shows_two_option_fields(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="options"', count=2)

    def test_successful_creation(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url, poll_data(description="Bütçem 300 TL", options=["Sinema", "Restoran", "Evde kal"])
        )
        poll = Poll.objects.get()
        self.assertRedirects(response, reverse("polls:detail", args=[poll.pk]), fetch_redirect_response=False)
        self.assertEqual(poll.author, self.user)
        self.assertEqual(poll.description, "Bütçem 300 TL")
        self.assertEqual(
            [(o.position, o.text) for o in poll.options.all()],
            [(0, "Sinema"), (1, "Restoran"), (2, "Evde kal")],
        )

    def test_success_message_is_shown_on_detail_page(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, poll_data(), follow=True)
        self.assertContains(response, "Anketin yayında! Linki paylaş, oylar gelsin.")

    def test_poll_appears_at_top_of_feed(self):
        make_poll(self.user, question="Eski anket")
        self.client.force_login(self.user)
        self.client.post(self.url, poll_data(question="Yeni anket sorusu"))
        polls = list(self.client.get(reverse("polls:feed")).context["page"])
        self.assertEqual(polls[0].question, "Yeni anket sorusu")

    def test_texts_are_trimmed(self):
        self.client.force_login(self.user)
        self.client.post(
            self.url, poll_data(question="  Soru metni  ", description="  açıklama  ", options=["  Bir ", " İki  "])
        )
        poll = Poll.objects.get()
        self.assertEqual((poll.question, poll.description), ("Soru metni", "açıklama"))
        self.assertEqual([o.text for o in poll.options.all()], ["Bir", "İki"])

    def test_blank_options_are_ignored(self):
        self.client.force_login(self.user)
        self.client.post(self.url, poll_data(options=["Bir", "", "  ", "İki", ""]))
        poll = Poll.objects.get()
        self.assertEqual([(o.position, o.text) for o in poll.options.all()], [(0, "Bir"), (1, "İki")])

    def assert_rejected(self, response, message):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, message)
        self.assertEqual(Poll.objects.count(), 0)
        self.assertEqual(Option.objects.count(), 0)

    def test_one_option_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, poll_data(options=["Sadece biri", "", ""]))
        self.assert_rejected(response, "En az 2 seçenek girmelisin.")

    def test_six_options_are_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, poll_data(options=["1", "2", "3", "4", "5", "6"]))
        self.assert_rejected(response, "En fazla 5 seçenek ekleyebilirsin.")

    def test_duplicate_options_are_rejected_case_insensitively(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, poll_data(options=["Sinema", "sinema"]))
        self.assert_rejected(response, "Aynı seçeneği birden fazla kez ekleyemezsin.")

    def test_too_long_option_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, poll_data(options=["a" * 81, "b"]))
        self.assert_rejected(response, "Her seçenek en fazla 80 karakter olabilir.")

    def test_empty_and_short_questions_are_rejected(self):
        self.client.force_login(self.user)
        self.assert_rejected(self.client.post(self.url, poll_data(question="")), "Soru boş olamaz.")
        self.assert_rejected(self.client.post(self.url, poll_data(question="    ")), "Soru boş olamaz.")
        self.assert_rejected(self.client.post(self.url, poll_data(question="abcd")), "Soru en az 5 karakter olmalı.")

    def test_too_long_question_and_description_are_rejected(self):
        self.client.force_login(self.user)
        self.assert_rejected(
            self.client.post(self.url, poll_data(question="a" * 201)), "Soru en fazla 200 karakter olabilir."
        )
        self.assert_rejected(
            self.client.post(self.url, poll_data(description="a" * 501)), "Açıklama en fazla 500 karakter olabilir."
        )

    def test_entered_data_is_kept_on_error(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            poll_data(question="Korunacak soru", description="Korunacak açıklama", options=["Sinema", "sinema", "Evde"]),
        )
        self.assertContains(response, "Korunacak soru")
        self.assertContains(response, "Korunacak açıklama")
        self.assertContains(response, 'value="Sinema"')
        self.assertContains(response, 'value="sinema"')
        self.assertContains(response, 'value="Evde"')
        self.assertContains(response, 'name="options"', count=3)

    def test_creation_is_atomic(self):
        self.client.force_login(self.user)
        # Seçenek kaydı patlarsa anket de kaydedilmemeli
        with mock.patch("polls.views.Option.objects.bulk_create", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                self.client.post(self.url, poll_data())
        self.assertEqual(Poll.objects.count(), 0)


class FeedTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ali@mail.com", "ali", PASSWORD)

    def test_empty_state(self):
        response = self.client.get(reverse("polls:feed"))
        self.assertContains(response, "Henüz anket yok. İlk kararsızlığı sen paylaş!")

    def test_cards_show_author_username_and_relative_time(self):
        make_poll(self.user, question="Kahve mi çay mı?", options=("Kahve", "Çay"))
        response = self.client.get(reverse("polls:feed"))
        self.assertContains(response, "@ali")
        self.assertContains(response, "Kahve mi çay mı?")
        self.assertContains(response, "az önce")
        self.assertNotContains(response, "ali@mail.com")

    def test_visitor_sees_welcome_card_but_member_does_not(self):
        self.assertContains(self.client.get(reverse("polls:feed")), "Hemen üye ol")
        self.client.force_login(self.user)
        self.assertNotContains(self.client.get(reverse("polls:feed")), "Hemen üye ol")

    def test_pagination_with_eleven_polls(self):
        for i in range(11):
            make_poll(self.user, question=f"Anket numara {i:02d}")
        first = self.client.get(reverse("polls:feed"))
        self.assertEqual(len(first.context["page"]), 10)
        self.assertContains(first, "Eski anketler")
        self.assertContains(first, "Anket numara 10")  # en yeni üstte
        self.assertNotContains(first, "Anket numara 00")

        second = self.client.get(reverse("polls:feed") + "?sayfa=2")
        self.assertEqual(len(second.context["page"]), 1)
        self.assertContains(second, "Anket numara 00")
        self.assertContains(second, "Yeni anketler")

    def test_invalid_page_number_does_not_crash(self):
        make_poll(self.user)
        for value in ["abc", "999", "-1", "0"]:
            self.assertEqual(self.client.get(reverse("polls:feed") + f"?sayfa={value}").status_code, 200, value)

    def test_feed_query_count_is_constant(self):
        # Sayfalama için COUNT + anketler (yazarla JOIN) + seçenekler = 3 sorgu
        for i in range(3):
            make_poll(self.user, question=f"Anket {i} sorusu", options=("A", "B", "C"))
        with self.assertNumQueries(3):
            self.client.get(reverse("polls:feed"))
        for i in range(9):
            make_poll(self.user, question=f"Başka anket {i}", options=("A", "B", "C", "D"))
        with self.assertNumQueries(3):
            self.client.get(reverse("polls:feed"))


class PollDetailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ali@mail.com", "ali", PASSWORD)

    def test_detail_page(self):
        poll = make_poll(
            self.user, question="Detay sorusu?", options=("Bir", "İki", "Üç"), description="Açıklama burada"
        )
        response = self.client.get(reverse("polls:detail", args=[poll.pk]))
        self.assertEqual(response.status_code, 200)
        for text in ["Detay sorusu?", "Bir", "İki", "Üç", "Açıklama burada", "@ali"]:
            self.assertContains(response, text)
        self.assertContains(response, "<title>Detay sorusu? — kararsızım</title>", html=True)

    def test_missing_poll_returns_404(self):
        self.assertEqual(self.client.get(reverse("polls:detail", args=[9999])).status_code, 404)

    def test_html_in_question_is_escaped(self):
        poll = make_poll(self.user, question="<script>alert(1)</script> soru", options=("<b>x</b>", "y"))
        response = self.client.get(reverse("polls:detail", args=[poll.pk]))
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertNotContains(response, "<b>x</b>")


class TemplateTagTests(TestCase):
    def test_time_ago(self):
        now = timezone.now()
        self.assertEqual(time_ago(now - timedelta(seconds=10)), "az önce")
        self.assertIn("dakika önce", time_ago(now - timedelta(minutes=5, seconds=5)))
        self.assertIn("saat önce", time_ago(now - timedelta(hours=2, minutes=10)))
        self.assertTrue(time_ago(now - timedelta(days=3, hours=2)).endswith("önce"))

    def test_avatar_color_is_stable_and_in_range(self):
        for name in ["ali", "ayse_01", "x.y"]:
            self.assertEqual(avatar_color(name), avatar_color(name))
            self.assertIn(avatar_color(name), range(1, 6))
