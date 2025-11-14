from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView

from .forms import UserRegisterForm, UserProfileForm

User = get_user_model()


class RegisterView(CreateView):
    """
    Регистрация нового пользователя.
    """

    model = User
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Страница профиля текущего пользователя.
    """

    template_name = "users/profile.html"


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Редактирование профиля текущего пользователя.
    """

    model = User
    form_class = UserProfileForm
    template_name = "users/profile_form.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user
