from twilio.rest import Client
from django.conf import settings

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def send_whatsapp_notification(recipient, message):
    if not recipient.startswith("whatsapp:"):
        recipient = f"whatsapp:{recipient}"
    client.messages.create(
        body=message,
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        to=recipient
    )