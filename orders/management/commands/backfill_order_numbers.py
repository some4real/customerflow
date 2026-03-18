from django.core.management.base import BaseCommand
from django.db.models import Max
from orders.models import Order


class Command(BaseCommand):
    help = 'Backfill order_number for existing orders with ORD- prefix format'

    def handle(self, *args, **options):
        # Get all orders, sorted by organization and creation date
        all_orders = Order.objects.all().order_by('organization', 'created_at')
        
        if not all_orders.exists():
            self.stdout.write(self.style.SUCCESS('No orders to process'))
            return
        
        # Group orders by organization
        orgs = {}
        for order in all_orders:
            org_id = order.organization_id
            if org_id not in orgs:
                orgs[org_id] = []
            orgs[org_id].append(order)
        
        # Assign order numbers for each organization with ORD- prefix
        total_updated = 0
        for org_id, org_orders in orgs.items():
            # Assign sequential numbers with ORD- prefix
            for index, order in enumerate(org_orders, start=1):
                new_order_num = f"ORD-{index}"
                if order.order_number != new_order_num:
                    order.order_number = new_order_num
                    order.save()
                    total_updated += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {total_updated} orders with ORD- prefix')
        )
