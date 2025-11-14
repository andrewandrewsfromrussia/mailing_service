from typing import Any
from django.contrib import messages as ui_messages
from django.forms import Form
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import MailingForm
from .models import Attempt, Client, Mailing, Message


class OwnerQuerySetMixin(LoginRequiredMixin):
    """
    Ограничивает queryset объектами текущего пользователя.
    """

    owner_field = "owner"

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()
        return qs.filter(**{self.owner_field: self.request.user})


class OwnerFormMixin:
    """
    Проставляет owner при создании.
    """

    owner_field = "owner"

    def form_valid(self, form: Form) -> HttpResponse:
        if not getattr(form.instance, self.owner_field, None):
            setattr(form.instance, self.owner_field, self.request.user)
        return super().form_valid(form)


# ---- Клиенты ----


class ClientListView(OwnerQuerySetMixin, ListView):
    model = Client
    template_name = "mailings/client_list.html"
    context_object_name = "clients"


class ClientCreateView(LoginRequiredMixin, OwnerFormMixin, CreateView):
    model = Client
    fields = ["email", "full_name", "comment"]  # owner ставится автоматически
    template_name = "mailings/client_form.html"
    success_url = reverse_lazy("mailings:client_list")


class ClientUpdateView(OwnerQuerySetMixin, UpdateView):
    model = Client
    fields = ["email", "full_name", "comment"]
    template_name = "mailings/client_form.html"
    success_url = reverse_lazy("mailings:client_list")


class ClientDeleteView(OwnerQuerySetMixin, DeleteView):
    model = Client
    template_name = "mailings/client_confirm_delete.html"
    success_url = reverse_lazy("mailings:client_list")


# ---- Сообщения ----


class MessageListView(OwnerQuerySetMixin, ListView):
    model = Message
    template_name = "mailings/message_list.html"
    context_object_name = "messages"


class MessageCreateView(LoginRequiredMixin, OwnerFormMixin, CreateView):
    model = Message
    fields = ["subject", "body"]
    template_name = "mailings/message_form.html"
    success_url = reverse_lazy("mailings:message_list")


class MessageUpdateView(OwnerQuerySetMixin, UpdateView):
    model = Message
    fields = ["subject", "body"]
    template_name = "mailings/message_form.html"
    success_url = reverse_lazy("mailings:message_list")


class MessageDeleteView(OwnerQuerySetMixin, DeleteView):
    model = Message
    template_name = "mailings/message_confirm_delete.html"
    success_url = reverse_lazy("mailings:message_list")


# ---- Рассылки ----


class MailingListView(OwnerQuerySetMixin, ListView):
    model = Mailing
    template_name = "mailings/mailing_list.html"
    context_object_name = "mailings"


class MailingCreateView(LoginRequiredMixin, OwnerFormMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:mailing_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["message"].queryset = Message.objects.filter(
            owner=self.request.user
        )
        form.fields["clients"].queryset = Client.objects.filter(owner=self.request.user)
        return form


class MailingUpdateView(OwnerQuerySetMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:mailing_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["message"].queryset = Message.objects.filter(
            owner=self.request.user
        )
        form.fields["clients"].queryset = Client.objects.filter(owner=self.request.user)
        return form


class MailingDeleteView(OwnerQuerySetMixin, DeleteView):
    model = Mailing
    template_name = "mailings/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailings:mailing_list")


class MailingRunView(OwnerQuerySetMixin, UpdateView):
    model = Mailing

    def post(self, request, *args, **kwargs):
        mailing = self.get_object()
        now = timezone.now()
        if mailing.start_at > now or mailing.finish_at < now:
            ui_messages.warning(request, "Сейчас не время для этой рассылки.")
            return redirect("mailings:mailing_list")

        sent, errors = 0, 0
        for client in mailing.clients.all():
            try:
                send_mail(
                    subject=mailing.message.subject,
                    message=mailing.message.body,
                    from_email=None,
                    recipient_list=[client.email],
                    fail_silently=False,
                )
                mailing.attempts.create(
                    client=client, is_success=True, server_response="OK"
                )
                sent += 1
            except Exception as e:
                mailing.attempts.create(
                    client=client, is_success=False, server_response=str(e)
                )
                errors += 1

        mailing.status = mailing.Status.FINISHED
        mailing.save(update_fields=["status"])
        ui_messages.success(request, f"Отправлено {sent}, ошибок {errors}")
        return redirect("mailings:mailing_list")


# @method_decorator(cache_page(60), name="dispatch")
class DashboardView(TemplateView):
    template_name = "mailings/dashboard.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if not user.is_authenticated:
            ctx.update(
                total_mailings=0,
                active_mailings=0,
                unique_clients=0,
                last_attempts=[],
                success_count=0,
                error_count=0,
            )
            return ctx

        qs_m = Mailing.objects.filter(owner=user)
        qs_c = Client.objects.filter(owner=user)
        qs_a = Attempt.objects.filter(mailing__owner=user).select_related(
            "client", "mailing"
        )[:10]

        now_active = qs_m.filter(status=Mailing.Status.RUNNING).count()
        success_count = Attempt.objects.filter(
            mailing__owner=user, is_success=True
        ).count()
        error_count = Attempt.objects.filter(
            mailing__owner=user, is_success=False
        ).count()

        ctx.update(
            total_mailings=qs_m.count(),
            active_mailings=now_active,
            unique_clients=qs_c.distinct().count(),
            last_attempts=qs_a,
            success_count=success_count,
            error_count=error_count,
        )
        return ctx
