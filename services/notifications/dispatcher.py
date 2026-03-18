import logging
from django.db import transaction
from notifications.models import NotificationLog
from .tasks import send_notification_task

logger = logging.getLogger(__name__)

CHANNELS = {
    "email": {
        "check": lambda c: c.email and getattr(getattr(c, "notification_preference", None), "email_enabled", True)
    },
    "sms": {
        "check": lambda c: c.phone and getattr(getattr(c, "notification_preference", None), "sms_enabled", True)
    },
    "whatsapp": {
        "check": lambda c: c.phone and getattr(getattr(c, "notification_preference", None), "whatsapp_enabled", True)
    },
}

def dispatch_order_notification(order, message, channels=None, force_all_channels=False):

    if not order or not order.customer:
        return

    if not message:
        return

    if channels is None:
        channels = ["email", "sms", "whatsapp"]

    def _send():
        for channel in channels:

            if channel not in CHANNELS:
                raise ValueError(f"Invalid notification channel: {channel}")

            if not force_all_channels and not CHANNELS[channel]["check"](order.customer):
                continue

            # Determine recipient
            if channel == "email":
                recipient = order.customer.email
                if not recipient:
                    continue
            else:
                recipient = order.customer.phone
                if not recipient:
                    continue

                if channel == "whatsapp" and not recipient.startswith("whatsapp:"):
                    recipient = f"whatsapp:{recipient}"

            logger.info(f"Dispatching {channel} notification for Order {order.order_number}")

            # Create log
            log = NotificationLog.objects.create(
                order=order,
                channel=channel,
                status="pending"
            )

            # Queue async task
            try:
                send_notification_task.delay(channel, recipient, message, log.id)
            except Exception as e:
                log.status = "failed"
                log.error_message = str(e)
                log.save()

                logger.error(
                    f"Failed to queue {channel} notification for Order {order.order_number}: {e}",
                    exc_info=True
                )

    transaction.on_commit(_send)