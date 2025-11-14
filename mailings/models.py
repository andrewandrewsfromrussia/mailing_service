from django.conf import settings
from django.db import models


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Client(TimeStamped):
    email = models.EmailField(unique=True)
    full_name = models.CharField("ФИО", max_length=255, blank=True)
    comment = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="clients"
    )

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"
        ordering = ("email",)

    def __str__(self):
        return self.email


class Message(TimeStamped):
    subject = models.CharField("Тема письма", max_length=255)
    body = models.TextField("Тело письма")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messages"
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ("-created_at",)

    def __str__(self):
        return self.subject


class Mailing(TimeStamped):
    class Status(models.TextChoices):
        CREATED = "создана", "Создана"
        RUNNING = "запущена", "Запущена"
        FINISHED = "завершена", "Завершена"

    start_at = models.DateTimeField("Дата и время первой отправки")
    finish_at = models.DateTimeField("Дата и время окончания отправки")
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.CREATED
    )

    message = models.ForeignKey(
        Message, on_delete=models.PROTECT, related_name="mailings"
    )
    clients = models.ManyToManyField(Client, related_name="mailings", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mailings"
    )

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["start_at"]),
            models.Index(fields=["finish_at"]),
        ]

    def __str__(self):
        return f"Рассылка #{self.pk} ({self.get_status_display()})"


class Attempt(models.Model):
    mailing = models.ForeignKey(
        Mailing, on_delete=models.CASCADE, related_name="attempts"
    )
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="attempts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_success = models.BooleanField(default=False)
    server_response = models.TextField(blank=True)

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылок"
        ordering = ("-created_at",)

    def __str__(self):
        s = "успех" if self.is_success else "ошибка"
        return f"{self.created_at:%Y-%m-%d %H:%M} — {s} для {self.client.email}"
