from django.contrib import admin

from .models import Option, Poll, Vote


class OptionInline(admin.TabularInline):
    model = Option
    extra = 0
    min_num = 2
    max_num = 5


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ("question", "author", "created_at")
    search_fields = ("question", "author__username")
    list_select_related = ("author",)
    inlines = [OptionInline]


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    """Oylar salt okunur: moderasyon için görüntülenir, elle eklenip değiştirilmez."""

    list_display = ("poll", "option", "user", "created_at")
    list_select_related = ("poll", "option", "user")
    readonly_fields = ("poll", "option", "user", "voter_token", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
