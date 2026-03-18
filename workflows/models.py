from django.db import models
from organizations.models import Organization


class WorkflowStage(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=255)
    position = models.PositiveIntegerField()
    is_final = models.BooleanField(default=False)

    color = models.CharField(
        max_length=20,
        choices=[
            ("blue", "Blue"),
            ("light-blue", "Light Blue"),
            ("sky", "Sky Blue"),
            ("indigo", "Indigo"),
            ("emerald", "Green"),
            ("lime", "Lime"),
            ("yellow", "Yellow"),
            ("amber", "Amber"),
            ("orange", "Orange"),
            ("red", "Red"),
            ("rose", "Rose"),
            ("pink", "Pink"),
            ("fuchsia", "Fuchsia"),
            ("purple", "Purple"),
            ("violet", "Violet"),
            ("slate", "Gray"),
            ("zinc", "Zinc"),
            ("stone", "Stone")
        ],
        default="blue"
    )

    # 🔔 Customer notification
    customer_message = models.TextField(
        blank=True,
        null=True,
        help_text="Message to send to customer when order reaches this stage"
    )

    notification_channels = models.JSONField(
        default=list,
        blank=True,
        help_text="Channels to send notification (email, sms, whatsapp)"
    )

    auto_notify = models.BooleanField(
        default=True,
        help_text="Automatically send notification when order enters this stage"
    )

    # 🧠 Internal use
    internal_note = models.TextField(
        blank=True,
        null=True,
        help_text="Internal note for staff (not sent to customer)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position']
        unique_together = (
            ('organization', 'name'),
            ('organization', 'position')
        )

    def __str__(self):
        return self.name