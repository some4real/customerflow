from django.core.mail import send_mail
from django.conf import settings

def send_email_notification(recipient, message):
    send_mail(
        subject="Order Notification",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False
    )