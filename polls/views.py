from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import login_required_with_message

from .forms import PollCreateForm
from .models import Option, Poll

POLLS_PER_PAGE = 10


def poll_queryset():
    # select_related: yazarı aynı sorguda JOIN ile getirir; prefetch_related: seçenekleri tek ek sorguda getirir.
    # İkisi de "N+1 sorgu" sorununu önler (her anket için ayrı sorgu atılmaz).
    return Poll.objects.select_related("author").prefetch_related("options")


def feed(request):
    paginator = Paginator(poll_queryset(), POLLS_PER_PAGE)
    page = paginator.get_page(request.GET.get("sayfa"))  # geçersiz sayfa numarasında en yakın sayfayı verir
    return render(request, "polls/feed.html", {"page": page})


def poll_detail(request, pk):
    poll = get_object_or_404(poll_queryset(), pk=pk)
    return render(request, "polls/detail.html", {"poll": poll})


@login_required_with_message
def poll_create(request):
    form = PollCreateForm(request.POST if request.method == "POST" else None)

    if request.method == "POST" and form.is_valid():
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
