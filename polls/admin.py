from django.contrib import admin

from .models import Option, Poll


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
