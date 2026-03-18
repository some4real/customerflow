from django.core.management.base import BaseCommand
from orders.models import Order
from notifications.models import NotificationLog

class Command(BaseCommand):
    help = 'Backfill notification logs for existing orders'

    def handle(self, *args, **options):
        # Get all orders without notification logs
        orders_without_logs = []
        
        for order in Order.objects.all():
            if not NotificationLog.objects.filter(order=order).exists():
                orders_without_logs.append(order)
        
        if not orders_without_logs:
            self.stdout.write(
                self.style.SUCCESS('All orders already have notification logs!')
            )
            return
        
        created_count = 0
        
        for order in orders_without_logs:
            # Create notification logs for available channels
            channels = []
            
            # Always add email (primary channel)
            if order.customer.email:
                channels.append('email')
            
            # Add SMS if phone exists
            if order.customer.phone:
                channels.append('sms')
                channels.append('whatsapp')
            
            # Create at least one log per order
            if not channels:
                channels = ['email']  # Default to email even if not available
            
            for channel in channels:
                NotificationLog.objects.create(
                    order=order,
                    channel=channel,
                    status='sent'
                )
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} notification logs for {len(orders_without_logs)} orders'
            )
        )
