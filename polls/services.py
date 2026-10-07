from django.db import IntegrityError, transaction
from django.db.models import Q

from .models import Option, Vote


class AlreadyVoted(Exception):
    """Bu tarayıcı veya üye bu ankete zaten oy vermiş."""


class InvalidOption(Exception):
    """Seçenek yok ya da başka bir ankete ait."""


def get_existing_vote(poll, voter_token, user=None):
    """Aynı tarayıcıdan VEYA (giriş yapılmışsa) aynı üyeden gelmiş oyu döndürür."""
    condition = Q(voter_token=voter_token)
    if user is not None and user.is_authenticated:
        condition |= Q(user=user)
    return Vote.objects.filter(poll=poll).filter(condition).first()


def cast_vote(poll, option_id, voter_token, user=None):
    option = Option.objects.filter(pk=option_id, poll=poll).first()
    if option is None:
        raise InvalidOption

    if get_existing_vote(poll, voter_token, user):
        raise AlreadyVoted

    try:
        # İki istek aynı anda gelirse yukarıdaki kontrol ikisini de geçebilir;
        # asıl güvence veritabanı kısıtlarıdır (IntegrityError).
        with transaction.atomic():
            return Vote.objects.create(
                poll=poll,
                option=option,
                user=user if user is not None and user.is_authenticated else None,
                voter_token=voter_token,
            )
    except IntegrityError:
        raise AlreadyVoted


def compute_percents(counts):
    """
    Oy sayılarından, toplamı HER ZAMAN 100 olan tam sayı yüzdeler üretir
    (en büyük kalan yöntemi). Eşitlikte önce oyu fazla olan, o da eşitse
    listede önce gelen (position'ı küçük) seçenek fazladan puanı alır.
    """
    total = sum(counts)
    if total == 0:
        return [0] * len(counts)

    percents = [count * 100 // total for count in counts]
    remainders = [count * 100 % total for count in counts]
    shortfall = 100 - sum(percents)
    order = sorted(range(len(counts)), key=lambda i: (-remainders[i], -counts[i], i))
    for index in order[:shortfall]:
        percents[index] += 1
    return percents


def build_results(options, voted_option_id=None):
    """
    `vote_count` annotation'ı olan, position sırasındaki seçeneklerden sonuç satırları üretir.
    "Önde" rozeti sadece tek bir lider varken verilir (eşitlikte kimse önde değildir).
    """
    options = list(options)
    counts = [option.vote_count for option in options]
    percents = compute_percents(counts)
    top = max(counts, default=0)
    has_single_leader = top > 0 and counts.count(top) == 1

    return [
        {
            "option_id": option.pk,
            "text": option.text,
            "position": option.position,
            "color": option.position + 1,
            "votes": count,
            "percent": percent,
            "is_leader": has_single_leader and count == top,
            "is_mine": option.pk == voted_option_id,
        }
        for option, count, percent in zip(options, counts, percents)
    ]
