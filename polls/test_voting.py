import uuid

from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User

from .models import Option, Poll, Vote
from .services import compute_percents

PASSWORD = "gizli-parola-123"
JSON = {"Accept": "application/json"}


def make_poll(author, question="Sinema mı restoran mı?", options=("Sinema", "Restoran")):
    poll = Poll.objects.create(author=author, question=question)
    for position, text in enumerate(options):
        Option.objects.create(poll=poll, text=text, position=position)
    return poll


def vote_url(poll):
    return reverse("polls:vote", args=[poll.pk])


class VoterTokenMiddlewareTests(TestCase):
    def test_new_visitor_gets_cookie_with_security_attributes(self):
        response = self.client.get(reverse("polls:feed"))
        cookie = response.cookies["kz_voter"]
        uuid.UUID(cookie.value)  # geçerli bir UUID
        self.assertEqual(cookie["max-age"], 60 * 60 * 24 * 365)
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertTrue(cookie["secure"])  # testlerde DEBUG kapalı → production gibi

    def test_existing_valid_cookie_is_kept(self):
        self.client.get(reverse("polls:feed"))
        token = self.client.cookies["kz_voter"].value
        response = self.client.get(reverse("polls:feed"))
        self.assertNotIn("kz_voter", response.cookies)
        self.assertEqual(self.client.cookies["kz_voter"].value, token)

    def test_invalid_cookie_is_replaced(self):
        self.client.cookies["kz_voter"] = "bu-bir-uuid-degil"
        response = self.client.get(reverse("polls:feed"))
        uuid.UUID(response.cookies["kz_voter"].value)

    def test_cookie_is_not_readable_value_leak_in_html(self):
        response = self.client.get(reverse("polls:feed"))
        token = response.cookies["kz_voter"].value
        self.assertNotContains(response, token)


class VoteTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user("yazar@mail.com", "yazar", PASSWORD)
        self.poll = make_poll(self.author)
        self.sinema, self.restoran = self.poll.options.all()

    def post_vote(self, option, client=None, json=True, poll=None):
        client = client or self.client
        extra = {"headers": JSON} if json else {}
        return client.post(vote_url(poll or self.poll), {"option_id": option.pk}, **extra)

    def test_visitor_can_vote_and_gets_results(self):
        response = self.post_vote(self.sinema)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["total_votes"], 1)
        self.assertEqual(body["voted_option_id"], self.sinema.pk)
        self.assertEqual(
            [(r["text"], r["votes"], r["percent"]) for r in body["results"]],
            [("Sinema", 1, 100), ("Restoran", 0, 0)],
        )
        vote = Vote.objects.get()
        self.assertIsNone(vote.user)
        self.assertEqual(str(vote.voter_token), self.client.cookies["kz_voter"].value)

    def test_member_vote_stores_user_and_token(self):
        member = User.objects.create_user("uye@mail.com", "uye", PASSWORD)
        self.client.force_login(member)
        self.post_vote(self.restoran)
        vote = Vote.objects.get()
        self.assertEqual(vote.user, member)
        self.assertEqual(str(vote.voter_token), self.client.cookies["kz_voter"].value)

    def test_second_vote_from_same_browser_is_rejected_and_counts_unchanged(self):
        self.post_vote(self.sinema)
        response = self.post_vote(self.restoran)
        self.assertEqual(response.status_code, 409)
        body = response.json()
        self.assertFalse(body["ok"])
        self.assertEqual(body["voted_option_id"], self.sinema.pk)  # önceki oy
        self.assertEqual(body["total_votes"], 1)
        self.assertEqual(Vote.objects.count(), 1)

    def test_same_member_from_different_browser_cannot_vote_twice(self):
        member = User.objects.create_user("uye@mail.com", "uye", PASSWORD)
        first_browser, second_browser = Client(), Client()
        first_browser.force_login(member)
        second_browser.force_login(member)
        self.assertEqual(self.post_vote(self.sinema, client=first_browser).status_code, 200)

        response = self.post_vote(self.restoran, client=second_browser)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["voted_option_id"], self.sinema.pk)
        self.assertEqual(Vote.objects.count(), 1)

    def test_different_visitors_can_vote_on_same_poll(self):
        self.post_vote(self.sinema, client=Client())
        self.post_vote(self.sinema, client=Client())
        response = self.post_vote(self.restoran, client=Client())
        self.assertEqual(response.json()["total_votes"], 3)

    def test_same_browser_can_vote_on_different_polls(self):
        other = make_poll(self.author, question="Kahve mi çay mı?", options=("Kahve", "Çay"))
        self.post_vote(self.sinema)
        response = self.post_vote(other.options.first(), poll=other)
        self.assertEqual(response.status_code, 200)

    def test_option_of_another_poll_is_rejected_with_400(self):
        other = make_poll(self.author, question="Kahve mi çay mı?", options=("Kahve", "Çay"))
        response = self.client.post(vote_url(self.poll), {"option_id": other.options.first().pk}, headers=JSON)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])
        self.assertEqual(Vote.objects.count(), 0)

    def test_garbage_option_ids_are_rejected_with_400(self):
        for value in ["", "abc", "999999", "-1"]:
            response = self.client.post(vote_url(self.poll), {"option_id": value}, headers=JSON)
            self.assertEqual(response.status_code, 400, value)
        self.assertEqual(self.client.post(vote_url(self.poll), {}, headers=JSON).status_code, 400)
        self.assertEqual(Vote.objects.count(), 0)

    def test_missing_poll_returns_404_for_json_and_html(self):
        url = reverse("polls:vote", args=[9999])
        self.assertEqual(self.client.post(url, {"option_id": 1}, headers=JSON).status_code, 404)
        self.assertEqual(self.client.post(url, {"option_id": 1}).status_code, 404)

    def test_vote_endpoint_is_post_only(self):
        self.assertEqual(self.client.get(vote_url(self.poll)).status_code, 405)

    def test_form_post_without_json_redirects_to_detail_with_message(self):
        response = self.post_vote(self.sinema, json=False)
        self.assertRedirects(
            response, reverse("polls:detail", args=[self.poll.pk]), fetch_redirect_response=False
        )
        page = self.client.get(reverse("polls:detail", args=[self.poll.pk]))
        self.assertContains(page, "Oyun kaydedildi!")
        self.assertEqual(Vote.objects.count(), 1)

    def test_second_form_post_shows_already_voted_message(self):
        self.post_vote(self.sinema, json=False)
        response = self.post_vote(self.restoran, json=False)
        self.assertEqual(response.status_code, 302)
        page = self.client.get(reverse("polls:detail", args=[self.poll.pk]))
        self.assertContains(page, "Bu ankete zaten oy verdin.")
        self.assertEqual(Vote.objects.count(), 1)

    def test_csrf_is_enforced(self):
        strict = Client(enforce_csrf_checks=True)
        response = strict.post(vote_url(self.poll), {"option_id": self.sinema.pk})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Vote.objects.count(), 0)

    def test_json_response_never_contains_email_or_token(self):
        member = User.objects.create_user("gizli.uye@mail.com", "uye", PASSWORD)
        self.client.force_login(member)
        response = self.post_vote(self.sinema)
        text = response.content.decode()
        self.assertNotIn("@mail.com", text)
        self.assertNotIn(self.client.cookies["kz_voter"].value, text)
        self.assertNotIn(self.client.cookies["kz_voter"].value.replace("-", ""), text)

    def test_database_constraints_block_duplicates_directly(self):
        from django.db import IntegrityError, transaction

        token = uuid.uuid4()
        Vote.objects.create(poll=self.poll, option=self.sinema, voter_token=token)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Vote.objects.create(poll=self.poll, option=self.restoran, voter_token=token)

        member = User.objects.create_user("uye@mail.com", "uye", PASSWORD)
        Vote.objects.create(poll=self.poll, option=self.sinema, voter_token=uuid.uuid4(), user=member)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Vote.objects.create(poll=self.poll, option=self.restoran, voter_token=uuid.uuid4(), user=member)

        # user=NULL olan oylar birbirini engellememeli
        Vote.objects.create(poll=self.poll, option=self.sinema, voter_token=uuid.uuid4())
        Vote.objects.create(poll=self.poll, option=self.sinema, voter_token=uuid.uuid4())

    def test_deleting_user_keeps_votes(self):
        member = User.objects.create_user("uye@mail.com", "uye", PASSWORD)
        Vote.objects.create(poll=self.poll, option=self.sinema, voter_token=uuid.uuid4(), user=member)
        member.delete()
        vote = Vote.objects.get()
        self.assertIsNone(vote.user)


class ResultVisibilityTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user("yazar@mail.com", "yazar", PASSWORD)
        self.poll = make_poll(self.author, options=("Sinema", "Restoran", "Evde kal"))
        self.detail = reverse("polls:detail", args=[self.poll.pk])
        # Başka tarayıcılardan 3 oy: Sinema 2, Restoran 1
        for option in [self.poll.options.all()[0], self.poll.options.all()[0], self.poll.options.all()[1]]:
            Client().post(vote_url(self.poll), {"option_id": option.pk}, headers=JSON)

    def test_visitor_who_has_not_voted_sees_buttons_and_total_but_no_percentages(self):
        response = self.client.get(self.detail)
        self.assertContains(response, "3 oy")
        self.assertContains(response, 'name="option_id"', count=3)
        self.assertNotContains(response, "result__percent")
        self.assertNotContains(response, "önde")
        self.assertNotContains(response, "%67")

    def test_voter_sees_result_bars_checkmark_and_leader_badge(self):
        option = self.poll.options.all()[2]  # Evde kal: 1 oy
        self.client.post(vote_url(self.poll), {"option_id": option.pk}, headers=JSON)
        response = self.client.get(self.detail)
        self.assertContains(response, "4 oy")
        self.assertContains(response, "result__percent", count=3)
        self.assertContains(response, "önde 🔥", count=1)
        self.assertContains(response, "result__check", count=1)
        self.assertNotContains(response, 'name="option_id"')  # artık oy butonu yok

    def test_results_persist_after_reload(self):
        option = self.poll.options.all()[1]
        self.client.post(vote_url(self.poll), {"option_id": option.pk}, headers=JSON)
        first = self.client.get(self.detail)
        second = self.client.get(self.detail)
        self.assertContains(first, "result__percent")
        self.assertContains(second, "result__percent")

    def test_owner_sees_results_without_voting_and_can_still_vote(self):
        self.client.force_login(self.author)
        response = self.client.get(self.detail)
        self.assertContains(response, "result__percent", count=3)
        self.assertContains(response, "önde 🔥", count=1)
        self.assertNotContains(response, "result__check")
        # satırlar oy butonu olarak çalışır
        self.assertContains(response, 'name="option_id"', count=3)

        option = self.poll.options.all()[2]
        response = self.client.post(vote_url(self.poll), {"option_id": option.pk}, headers=JSON)
        self.assertEqual(response.status_code, 200)
        self.assertContains(self.client.get(self.detail), "result__check", count=1)

    def test_no_leader_badge_on_tie(self):
        poll = make_poll(self.author, question="Eşitlik sorusu?", options=("A", "B"))
        a, b = poll.options.all()
        Client().post(vote_url(poll), {"option_id": a.pk}, headers=JSON)
        Client().post(vote_url(poll), {"option_id": b.pk}, headers=JSON)
        self.client.force_login(self.author)
        response = self.client.get(reverse("polls:detail", args=[poll.pk]))
        self.assertNotContains(response, "önde 🔥")

    def test_voted_state_is_shared_between_feed_and_detail(self):
        option = self.poll.options.all()[0]
        self.client.post(vote_url(self.poll), {"option_id": option.pk}, headers=JSON)
        feed = self.client.get(reverse("polls:feed"))
        self.assertContains(feed, "result__percent", count=3)
        self.assertContains(feed, "result__check", count=1)


class PercentTests(TestCase):
    def test_percentages_always_sum_to_100(self):
        for counts in [[15, 9], [1, 1, 1], [1, 1, 1, 1, 1], [7, 3, 3], [0, 0], [5, 0], [1, 2, 4, 8, 16], [33, 33, 34]]:
            percents = compute_percents(counts)
            expected = 0 if sum(counts) == 0 else 100
            self.assertEqual(sum(percents), expected, counts)

    def test_documented_example(self):
        self.assertEqual(compute_percents([15, 9]), [63, 37])

    def test_tie_goes_to_higher_votes_then_earlier_position(self):
        self.assertEqual(compute_percents([1, 1, 1]), [34, 33, 33])
        self.assertEqual(compute_percents([2, 1]), [67, 33])

    def test_zero_votes_gives_zero_percents(self):
        self.assertEqual(compute_percents([0, 0, 0]), [0, 0, 0])


class PollDeleteTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user("yazar@mail.com", "yazar", PASSWORD)
        self.other = User.objects.create_user("baska@mail.com", "baska", PASSWORD)
        self.poll = make_poll(self.author)
        self.url = reverse("polls:delete", args=[self.poll.pk])

    def test_owner_can_delete_and_votes_go_with_it(self):
        Client().post(vote_url(self.poll), {"option_id": self.poll.options.first().pk}, headers=JSON)
        self.client.force_login(self.author)
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, reverse("polls:feed"))
        self.assertContains(response, "Anketin silindi.")
        self.assertEqual(Poll.objects.count(), 0)
        self.assertEqual(Option.objects.count(), 0)
        self.assertEqual(Vote.objects.count(), 0)

    def test_non_owner_gets_404_and_poll_survives(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.assertEqual(Poll.objects.count(), 1)

    def test_visitor_gets_404_and_poll_survives(self):
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.assertEqual(Poll.objects.count(), 1)

    def test_delete_requires_post(self):
        self.client.force_login(self.author)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertEqual(Poll.objects.count(), 1)

    def test_delete_button_only_visible_to_owner_and_asks_for_confirmation(self):
        detail = reverse("polls:detail", args=[self.poll.pk])
        self.assertNotContains(self.client.get(detail), self.url)
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(detail), self.url)
        self.client.force_login(self.author)
        response = self.client.get(detail)
        self.assertContains(response, self.url)
        self.assertContains(response, "Bu anketi silmek istediğine emin misin?")


class FeedVotingQueryTests(TestCase):
    def test_feed_query_count_does_not_grow_with_polls_or_votes(self):
        author = User.objects.create_user("yazar@mail.com", "yazar", PASSWORD)
        member = User.objects.create_user("uye@mail.com", "uye", PASSWORD)
        self.client.force_login(member)

        def add_polls(count):
            for i in range(count):
                poll = make_poll(author, question=f"Soru numara {i}?", options=("A", "B", "C"))
                for option in poll.options.all()[:2]:
                    Vote.objects.create(poll=poll, option=option, voter_token=uuid.uuid4())

        add_polls(2)
        self.client.get(reverse("polls:feed"))  # çerez + oturum ilk istekte kurulsun
        with self.assertNumQueries(6) as small:
            self.client.get(reverse("polls:feed"))
        add_polls(8)
        with self.assertNumQueries(6):
            response = self.client.get(reverse("polls:feed"))
        self.assertEqual(len(response.context["page"]), 10)
        self.assertEqual(len(small), 6)

    def test_detail_query_count_is_small(self):
        author = User.objects.create_user("yazar@mail.com", "yazar", PASSWORD)
        poll = make_poll(author)
        # anket + seçenekler + ziyaretçinin oyu
        with self.assertNumQueries(3):
            self.client.get(reverse("polls:detail", args=[poll.pk]))
