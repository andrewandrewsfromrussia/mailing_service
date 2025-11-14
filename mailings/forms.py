from django import forms

from .models import Mailing


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ["start_at", "finish_at", "status", "message", "clients"]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "finish_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
