# services/notifications/signals.py

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from orders.models import Order
from services.notifications.dispatcher import dispatch_order_notification

@receiver(pre_save, sender=Order)
def track_order_status(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old_order = Order.objects.get(pk=instance.pk)
        instance._old_status = old_order.status
    except Order.DoesNotExist:
        instance._old_status = None

@receiver(post_save, sender=Order)
def notify_order_status(sender, instance, created, **kwargs):
    # Skip if batch update
    
    if hasattr(instance, "_skip_notification"):
        return

    old_status = getattr(instance, "_old_status", None)
    if old_status == instance.status:
        return  # No change

    # Prepare message
    stage = instance.status
    message = (
        stage.customer_message.format(
            customer_name=instance.customer.name,
            order_number=instance.order_number
        )
        if getattr(stage, "customer_message", None)
        else f"Order {instance.order_number} status updated: {stage.name}"
    )

    # Dispatch notifications
    dispatch_order_notification(instance, message)