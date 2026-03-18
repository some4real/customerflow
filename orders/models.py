from django.db import models, transaction
from django.conf import settings
from organizations.models import Organization
from customers.models import Customer
from workflows.models import WorkflowStage


class Order(models.Model):

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE
    )

    # Organization-specific order number
    order_number = models.CharField(max_length=50, null=True, blank=True)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # Current workflow stage
    status = models.ForeignKey(
        WorkflowStage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, user=None, **kwargs):

        is_new = self.pk is None

        # 🔹 Get old status efficiently (no full object load)
        old_status_id = None
        if self.pk:
            old_status_id = (
                Order.objects
                .filter(pk=self.pk)
                .values_list("status", flat=True)
                .first()
            )

        # Assign default workflow stage
        if not self.status:
            self.status = WorkflowStage.objects.filter(
                organization=self.organization
            ).order_by("position").first()

        # Generate order number safely (no duplicates)
        if not self.order_number:
            with transaction.atomic():
                last_order = (
                    Order.objects
                    .select_for_update()
                    .filter(
                        organization=self.organization,
                        order_number__startswith="ORD-"
                    )
                    .order_by("-id")
                    .first()
                )

                if last_order and last_order.order_number:
                    try:
                        current_num = int(last_order.order_number.replace("ORD-", ""))
                        next_num = current_num + 1
                    except ValueError:
                        next_num = 1
                else:
                    next_num = 1

                self.order_number = f"ORD-{next_num:05d}"

        super().save(*args, **kwargs)

        # Import here to avoid circular imports
        from orders.models import OrderActivity
        from services.notifications.dispatcher import dispatch_order_notification

        # Activity logging
        if is_new:
            OrderActivity.objects.create(
                order=self,
                message="Order created",
                type="system",
                created_by=user
            )

        elif old_status_id != self.status_id:

            OrderActivity.objects.create(
                order=self,
                message=f"Status changed to {self.status.name}",
                type="status_change",
                created_by=user
            )

            # Trigger notification (based on workflow stage)
            if self.status and getattr(self.status, "auto_notify", True):
                if self.status.customer_message:
                    dispatch_order_notification(
                        order=self,
                        message=self.status.customer_message,
                        channels=getattr(self.status, "notification_channels", None)
                    )

    class Meta:
        unique_together = ('organization', 'order_number')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"#{self.order_number} - {self.title} - {self.customer.name}"


# ACTIVITY / TIMELINE MODEL

class OrderActivity(models.Model):

    TYPE_CHOICES = [
        ("system", "System"),
        ("status_change", "Status Change"),
        ("notification", "Notification"),
        ("user_action", "User Action"),
    ]

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="activities"
    )

    message = models.TextField()

    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default="system"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.order.order_number} - {self.type}"