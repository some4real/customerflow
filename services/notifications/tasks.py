# services/notifications/tasks.py

from celery import shared_task
from notifications.models import NotificationLog
from .email_service import send_email_notification
from .sms_service import send_sms_notification
from .whatsapp_service import send_whatsapp_notification

CHANNEL_HANDLERS = {
    "email": send_email_notification,
    "sms": send_sms_notification,
    "whatsapp": send_whatsapp_notification,
}

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_notification_task(self, channel, recipient, message, log_id):
    try:
        log = NotificationLog.objects.get(id=log_id)
    except NotificationLog.DoesNotExist:
        # Log missing notification
        return

    try:
        CHANNEL_HANDLERS[channel](recipient, message)
        log.status = "sent"
        log.error_message = ""
    except Exception as exc:
        log.status = "failed"
        log.error_message = f"{type(exc).__name__}: {str(exc)}"
        log.save()
        raise self.retry(exc=exc)

    log.save()