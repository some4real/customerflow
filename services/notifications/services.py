# services/notifications/service.py

from notifications.models import NotificationLog
from .dispatcher import dispatch_order_notification

class NotificationService:
    @staticmethod
    def notify_customer(order, message, channels=None):
        """
        Sends notifications to the customer across selected channels.
        Logs all attempts in NotificationLog.
        """
        dispatch_order_notification(order, message, channels)

    @staticmethod
    def get_customer_notifications(customer):
        """
        Retrieve all notifications sent to a customer for dashboard.
        """
        return NotificationLog.objects.filter(order__customer=customer)