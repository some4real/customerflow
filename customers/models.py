from django.db import models
from organizations.models import Organization
# Create your models here.

class Customer(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"


class CustomerNotificationPreference(models.Model):
    customer = models.OneToOneField("Customer", on_delete=models.CASCADE, related_name="notification_preference")
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    whatsapp_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification preferences for {self.customer}"