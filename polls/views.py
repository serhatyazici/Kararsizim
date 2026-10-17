from datetime import timedelta

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import login_required_with_message

from .forms import PollCreateForm
from .models import Option, Poll, Vote
from .services import (
    AlreadyVoted,
    InvalidOption,
    build_results,
    cast_vote,
    get_existing_vote,
)

POLLS_PER_PAGE = 10
# Spam'e karşı: bir üye son 1 saatte en fazla bu kadar anket açabilir
POLL_CREATE_LIMIT = 5
POLL_CREATE_WINDOW = timedelta(hours=1)


def poll_queryset():
    """
    Akış ve detay için ortak sorgu.
    - select_related: yazarı aynı sorguda JOIN ile getirir.
    - Prefetch + annotate: seçenekleri, oy sayılarıyla birlikte TEK ek sorguda getirir.
    İkisi de "N+1 sorgu" sorununu önler (her anket için ayrı sorgu atılmaz).
    Not: annotate'li sorgularda Meta.ordering yok sayılır, sıralamayı açıkça veriyoruz.
    """
    options = Option.objects.annotate(vote_count=Count("votes")).order_by("position")
    return (
        Poll.objects.select_related("author")
        .prefetch_related(Prefetch("options", queryset=options))
        .annotate(total_votes=Count("votes", distinct=True))
        .order_by("-created_at", "-pk")
    )


def prepare_polls(request, polls):
    """
    Kartların ihtiyaç duyduğu bilgileri her ankete ekler: ziyaretçinin oyu, sonuçların
    gösterilip gösterilmeyeceği ve sonuç satırları. Ziyaretçinin hangi anketlere
    oy verdiği TEK sorguda bulunur.
    """
    polls = list(polls)

    voted = {}
    if polls:
        condition = Q(voter_token=request.voter_token)
        if request.user.is_authenticated:
            condition |= Q(user=request.user)
        voted = dict(
            Vote.objects.filter(condition, poll__in=polls).values_list("poll_id", "option_id")
        )

    for poll in polls:
        poll.voted_option_id = voted.get(poll.pk)
        poll.is_owner = request.user.is_authenticated and poll.author_id == request.user.pk
        # Oy vermeyen yüzdeleri göremez (diğer oyların yönlendirme etkisini önlemek için); sahibi her zaman görür
        poll.show_results = poll.voted_option_id is not None or poll.is_owner
        poll.result_rows = build_results(poll.options.all(), poll.voted_option_id)
    return polls


def feed(request):
    paginator = Paginator(poll_queryset(), POLLS_PER_PAGE)
    paginator.count = Poll.objects.count()  # toplamı oy tablosuna JOIN atmadan, basit bir COUNT ile bul
    page = paginator.get_page(request.GET.get("sayfa"))  # geçersiz sayfa numarasında en yakın sayfayı verir
    prepare_polls(request, page)  # aynı nesneleri sayfa içinde günceller
    return render(request, "polls/feed.html", {"page": page})


def poll_detail(request, pk):
    poll = get_object_or_404(poll_queryset(), pk=pk)
    prepare_polls(request, [poll])
    return render(request, "polls/detail.html", {"poll": poll})


@login_required_with_message
def poll_create(request):
    form = PollCreateForm(request.POST if request.method == "POST" else None)

    if request.method == "POST" and form.is_valid():
        # Hız sınırı: formdaki veriler kaybolmasın diye hata olarak aynı form yeniden çizilir (429)
        recent_polls = Poll.objects.filter(
            author=request.user, created_at__gte=timezone.now() - POLL_CREATE_WINDOW
        ).count()
        if recent_polls >= POLL_CREATE_LIMIT:
            form.add_error(None, "Çok hızlı anket açıyorsun. Biraz bekleyip tekrar dene.")
            return render(request, "polls/create.html", {"form": form}, status=429)

        # transaction.atomic: içindeki işlemler ya hep birlikte kaydedilir ya da hiçbiri.
        # Anket kaydedilip seçenekler yazılamazsa yarım anket kalmaz.
        with transaction.atomic():
            poll = Poll.objects.create(
                author=request.user,
                question=form.cleaned_data["question"],
                description=form.cleaned_data["description"],
            )
            Option.objects.bulk_create(
                [
                    Option(poll=poll, text=text, position=position)
                    for position, text in enumerate(form.cleaned_options)
                ]
            )
        messages.success(request, "Anketin yayında! Linki paylaş, oylar gelsin.")
        return redirect("polls:detail", pk=poll.pk)

    return render(request, "polls/create.html", {"form": form})


def wants_json(request):
    return "application/json" in request.headers.get("Accept", "")


def results_payload(poll, voted_option_id):
    """JSON yanıtı (CLAUDE.md 8.3). E-posta gibi kişisel veri içermez."""
    options = poll.options.annotate(vote_count=Count("votes")).order_by("position")
    rows = build_results(options, voted_option_id)
    return {
        "total_votes": sum(row["votes"] for row in rows),
        "voted_option_id": voted_option_id,
        "results": [
            {
                "option_id": row["option_id"],
                "text": row["text"],
                "position": row["position"],
                "votes": row["votes"],
                "percent": row["percent"],
                "is_leader": row["is_leader"],
            }
            for row in rows
        ],
    }


@require_POST
def vote(request, pk):
    json_mode = wants_json(request)

    def fail(status, message, poll=None, voted_option_id=None):
        if json_mode:
            body = {"ok": False, "error": message}
            if poll is not None:
                body.update(results_payload(poll, voted_option_id))
            return JsonResponse(body, status=status)
        if status == 404:
            raise Http404(message)
        level = messages.info if status == 409 else messages.error
        level(request, message)
        return redirect("polls:detail", pk=pk)

    poll = Poll.objects.filter(pk=pk).first()
    if poll is None:
        return fail(404, "Anket bulunamadı.")

    try:
        option_id = int(request.POST.get("option_id", ""))
    except ValueError:
        return fail(400, "Geçersiz seçenek.")

    try:
        voted = cast_vote(poll, option_id, request.voter_token, request.user)
    except InvalidOption:
        return fail(400, "Geçersiz seçenek.")
    except AlreadyVoted:
        existing = get_existing_vote(poll, request.voter_token, request.user)
        return fail(
            409,
            "Bu ankete zaten oy verdin.",
            poll=poll,
            voted_option_id=existing.option_id if existing else None,
        )

    if json_mode:
        return JsonResponse({"ok": True, **results_payload(poll, voted.option_id)})
    messages.success(request, "Oyun kaydedildi! 🗳️")
    return redirect("polls:detail", pk=poll.pk)


@require_POST
def poll_delete(request, pk):
    # Sahibi olmayanın (ve ziyaretçinin) isteği 404 döner: anketin var olup olmadığı bile sızdırılmaz
    poll = get_object_or_404(Poll, pk=pk, author_id=request.user.pk)
    poll.delete()
    messages.success(request, "Anketin silindi.")
    return redirect("polls:feed")
