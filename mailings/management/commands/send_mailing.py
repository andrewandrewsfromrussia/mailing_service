import logging

from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from mailings.models import Mailing

logger = logging.getLogger("mailings")


class Command(BaseCommand):
    help = "Отправляет выбранную рассылку по ID и логирует попытки"

    def add_arguments(self, parser):
        parser.add_argument("mailing_id", type=int, help="ID рассылки")

    def handle(self, *args, **options):
        mailing_id = options["mailing_id"]

        try:
            mailing = (
                Mailing.objects.select_related("message")
                .prefetch_related("clients")
                .get(pk=mailing_id)
            )
        except Mailing.DoesNotExist as exc:
            logger.warning(
                "Попытка запустить несуществующую рассылку id=%s", mailing_id
            )
            raise CommandError(f"Рассылка #{mailing_id} не найдена") from exc

        logger.info("Запуск рассылки id=%s владельца=%s", mailing.pk, mailing.owner_id)

        now = timezone.now()
        if mailing.start_at > now or mailing.finish_at < now:
            logger.info(
                "Запрет запуска вне окна времени: now=%s, start=%s, finish=%s, id=%s",
                now,
                mailing.start_at,
                mailing.finish_at,
                mailing.pk,
            )
            self.stdout.write(self.style.WARNING("Сейчас не входит в окно отправки."))
            return

        sent = 0
        failed = 0

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
                logger.info("Отправлено: mailing=%s -> %s", mailing.pk, client.email)
            except Exception as e:
                mailing.attempts.create(
                    client=client, is_success=False, server_response=str(e)
                )
                failed += 1
                logger.error(
                    "Ошибка отправки: mailing=%s -> %s; error=%s",
                    mailing.pk,
                    client.email,
                    e,
                )

        mailing.status = Mailing.Status.FINISHED
        mailing.save(update_fields=["status"])

        logger.info(
            "Завершено: mailing=%s; успехов=%s; ошибок=%s", mailing.pk, sent, failed
        )
        self.stdout.write(
            self.style.SUCCESS(f"Готово. Успехов: {sent}, ошибок: {failed}")
        )
