from django.contrib import admin

from .models import Attempt, Client, Mailing, Message


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "owner", "created_at")
    search_fields = ("email", "full_name")
    list_filter = ("owner",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "owner", "created_at")
    search_fields = ("subject",)
    list_filter = ("owner",)


class AttemptInline(admin.TabularInline):
    model = Attempt
    extra = 0
    readonly_fields = ("created_at", "is_success", "server_response", "client")


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "start_at", "finish_at", "owner", "message")
    list_filter = ("status", "owner")
    date_hierarchy = "start_at"
    inlines = [AttemptInline]
    filter_horizontal = ("clients",)


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("mailing", "client", "created_at", "is_success")
    list_filter = ("is_success", "mailing")
    search_fields = ("client__email",)
