from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

User = get_user_model()


class UserRegisterForm(UserCreationForm):
    """
    Форма регистрации нового пользователя по email.
    Использует стандартную логику UserCreationForm (пароль, валидация и т.п.),
    но в качестве логина — поле email.
    """

    class Meta:
        model = User
        fields = ("email", "avatar", "phone", "country")


class UserProfileForm(UserChangeForm):
    """
    Форма редактирования профиля текущего пользователя.
    Поле пароля здесь не редактируется.
    """

    password = None

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "avatar", "phone", "country")
