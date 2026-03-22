import json
import logging
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from orders.models import Order, OrderActivity
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction

from .models import Order
from customers.models import Customer
from workflows.models import WorkflowStage
from notifications.models import NotificationLog
from services.notifications.dispatcher import dispatch_order_notification

logger = logging.getLogger(__name__)

@login_required
@require_POST
def bulk_update_orders(orders, status, user=None):
    """
    Bulk update orders with notifications and internal logs.
    """
    orders = list(orders.select_related("customer"))

    # Update in memory
    for order in orders:
        order.status = status
        order._skip_notification = True  # optional, prevent signal spam

    # Bulk update (single query)
    Order.objects.bulk_update(orders, ["status"])

    # Send notifications and log activity
    for order in orders:
        message = (
            status.customer_message.format(
                customer_name=order.customer.name,
                order_number=order.order_number
            )
            if status.customer_message
            else f"Order {order.order_number} status updated to {status.name}"
        )

        # Send notifications (email/SMS/WhatsApp)
        dispatch_order_notification(order, message, force_all_channels=True)

        # Log status change in OrderActivity
        OrderActivity.objects.create(
            order=order,
            message=f"Status changed to {status.name}",
            type="status_change",
            created_by=user
        )

class OrderListView(ListView):
    model = Order
    template_name = "orders/list.html"
    context_object_name = "orders"
    ordering = ["-created_at"]
    paginate_by = 20  

    def get_queryset(self):
        return Order.objects.filter(
            organization=self.request.user.organization
        ).select_related("customer", "status")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['available_statuses'] = WorkflowStage.objects.filter(
            organization=self.request.user.organization
        ).order_by('name')

        context['total_orders'] = Order.objects.filter(
            organization=self.request.user.organization
        ).count()

        return context


class OrderCreateView(CreateView):
    model = Order
    template_name = "orders/create.html"
    fields = ["title", "description", "customer", "status"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['customer'].queryset = Customer.objects.filter(
            organization=self.request.user.organization
        )

        form.fields['status'].queryset = WorkflowStage.objects.filter(
            organization=self.request.user.organization
        )

        return form

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("orders:list")

class OrderDetailView(DetailView):
    model = Order
    template_name = "orders/detail.html"
    context_object_name = "order"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return Order.objects.filter(
            organization=self.request.user.organization
        ).select_related("customer", "status")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        order = self.object

        # Fetch notifications
        notifications = NotificationLog.objects.filter(order=order).order_by('-timestamp')

        # Fetch order activities
        activities = OrderActivity.objects.filter(order=order).order_by('-created_at')

        # Build unified timeline
        timeline = []

        # Order Created
        timeline.append({
            "type": "user_action",
            "message": "Order created",
            "created_at": order.created_at,
            "user": None,
        })

        # Activities (status changes or other messages)
        for act in activities:
            if "status changed" in act.message.lower():
                timeline.append({
                    "type": "status_change",
                    "message": act.message,
                    "created_at": act.created_at,
                    "user": act.created_by.get_full_name() if act.created_by else None,
                })
            else:
                timeline.append({
                    "type": "user_action",
                    "message": act.message,
                    "created_at": act.created_at,
                    "user": act.created_by.get_full_name() if act.created_by else None,
                })

        # Notifications
        for notif in notifications:
            timeline.append({
                "type": "notification",
                "message": f"{notif.channel.title()} notification",
                "created_at": notif.timestamp,
                "status": notif.status,
                "channel": notif.channel,
                "user": None,
            })

        # Sort timeline newest first
        timeline.sort(key=lambda x: x["created_at"], reverse=True)

        context['timeline'] = timeline
        context['notifications'] = notifications
        return context


class OrderUpdateView(UpdateView):
    model = Order
    template_name = "orders/update.html"
    fields = ["title", "description", "customer", "status"]
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return Order.objects.filter(
            organization=self.request.user.organization
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['customer'].queryset = Customer.objects.filter(
            organization=self.request.user.organization
        )

        form.fields['status'].queryset = WorkflowStage.objects.filter(
            organization=self.request.user.organization
        )

        return form

    def get_success_url(self):
        return reverse("orders:detail", kwargs={"pk": self.object.pk})

def OrderDeleteView():
    pass  # Placeholder for future implementation


# AJAX ENDPOINTS

@login_required
@require_http_methods(["POST"])
def update_order_status(request):
    """
    Update a single order's status (AJAX) with:
    - Notification dispatch
    - Internal activity logging
    """
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        status_id = data.get('status_id')

        # Fetch order and workflow stage
        order = get_object_or_404(Order, id=order_id, organization=request.user.organization)
        status = get_object_or_404(WorkflowStage, id=status_id, organization=request.user.organization)

        # Update order
        order.status = status
        order.save(user=request.user)

        # Prepare message
        message = (
            status.customer_message.format(
                customer_name=order.customer.name,
                order_number=order.order_number
            )
            if status.customer_message else f"Order {order.order_number} status updated to {status.name}"
        )

        # Send notifications
        dispatch_order_notification(order, message, force_all_channels=True)

        # Log activity
        OrderActivity.objects.create(
            order=order,
            message=f"Status changed to {status.name}",
            type="status_change",
            created_by=request.user
        )

        return JsonResponse({
            'success': True,
            'message': f'Order {order.order_number} updated to {status.name}',
            'status_name': status.name
        })

    except Exception as e:
        logger.exception("Single status update failed")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required
@require_POST
def batch_update_status(request):
    try:
        data = json.loads(request.body)

        status_id = data.get("status_id")
        order_ids = data.get("order_ids", [])
        select_all = data.get("select_all", False)
        excluded_ids = data.get("excluded_ids", [])

        status = get_object_or_404(
            WorkflowStage,
            id=status_id,
            organization=request.user.organization
        )

        if select_all:
            orders = Order.objects.filter(
                organization=request.user.organization
            ).exclude(id__in=excluded_ids)
        else:
            orders = Order.objects.filter(
                id__in=order_ids,
                organization=request.user.organization
            )

        if not orders.exists():
            return JsonResponse({"success": False}, status=404)

        with transaction.atomic():
            for order in orders:
                order.status = status
                order.save(user=request.user)

                # ✅ Notification per order
                if status and getattr(status, "auto_notify", True):
                    message = (
                        status.customer_message.format(
                            customer_name=order.customer.name,
                            order_number=order.order_number
                        )
                        if status.customer_message
                        else f"Order {order.order_number} updated to {status.name}"
                    )

                    dispatch_order_notification(order, message, force_all_channels=True)

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
    

# Single Order Delete
class OrderDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            order = Order.objects.get(
                pk=pk,
                organization=request.user.organization
            )

            order_number = order.order_number


            order.delete()

            return JsonResponse({
                "success": True,
                "message": f"Order {order_number} deleted"
            })

        except Order.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "Order not found"
            }, status=404)
        

@login_required
@require_POST
def bulk_delete_orders(request):
    try:
        data = json.loads(request.body)

        select_all = data.get("select_all", False)
        excluded_ids = data.get("excluded_ids", [])
        order_ids = data.get("order_ids", [])

        if select_all:
            orders = Order.objects.filter(
                organization=request.user.organization
            ).exclude(id__in=excluded_ids)
        else:
            if not order_ids:
                return JsonResponse({
                    "success": False,
                    "message": "No orders selected"
                }, status=400)

            orders = Order.objects.filter(
                id__in=order_ids,
                organization=request.user.organization
            )

        if not orders.exists():
            return JsonResponse({
                "success": False,
                "message": "No valid orders found"
            }, status=404)

        order_numbers = list(
            orders.values_list("order_number", flat=True)
        )

        deleted_count = orders.count()

        # ✅ Wrap everything safely
        with transaction.atomic():

            # ✅ Bulk log BEFORE delete
            activities = [
                OrderActivity(
                    order=order,
                    message=f"Order {order.order_number} deleted",
                    type="deletion",
                    created_by=request.user
                )
                for order in orders
            ]
            OrderActivity.objects.bulk_create(activities)

            # ✅ Delete after logging
            orders.delete()

        return JsonResponse({
            "success": True,
            "deleted_count": deleted_count
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)