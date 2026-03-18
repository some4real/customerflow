from twilio.rest import Client
from django.conf import settings

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def send_sms_notification(recipient, message):
    client.messages.create(
        body=message,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=recipient
    )