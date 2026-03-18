from django.contrib.auth.models import AbstractUser
from django.db import models
from organizations.models import Organization
import secrets


class User(AbstractUser):

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    role = models.CharField(
        max_length=50,
        default="staff",
        choices=[
            ("admin", "Admin"),
            ("staff", "Staff"),
        ]
    )


class StaffInvitation(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE
    )
    
    email = models.EmailField()
    token = models.CharField(max_length=100, unique=True, default=secrets.token_urlsafe(32))
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="invitations_sent"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invitations_accepted"
    )

    class Meta:
        unique_together = ('organization', 'email')

    def __str__(self):
        return f"{self.email} - {self.organization.name}"
