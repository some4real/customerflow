from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse

from orders.models import Order
from customers.models import Customer
from notifications.models import NotificationLog
from workflows.models import WorkflowStage
from services.notifications.dispatcher import dispatch_order_notification  # assumes you have this service


def landing_view(request):
    return render(request, "landing.html")


@login_required
def dashboard_view(request):
    org = request.user.organization
    query = request.GET.get("q", "").strip()

    today = timezone.now().date()
    yesterday = today - timezone.timedelta(days=1)
    last_week = today - timezone.timedelta(days=7)
    last_month = today - timezone.timedelta(days=30)

    # --- Dashboard Metrics ---
    active_orders = Order.objects.filter(organization=org, status__is_final=False).count()
    delivered_today = Order.objects.filter(
        organization=org, status__is_final=True, updated_at__date=today
    ).count()
    total_customers = Customer.objects.filter(organization=org).count()
    notifications_sent = NotificationLog.objects.filter(order__organization=org).count()

    # --- Historical Data ---
    active_orders_last_week = Order.objects.filter(
        organization=org, created_at__date__gte=last_week
    ).exclude(status__is_final=True).count()
    delivered_yesterday = Order.objects.filter(
        organization=org, status__is_final=True, updated_at__date=yesterday
    ).count()
    total_customers_last_month = Customer.objects.filter(
        organization=org, created_at__date__gte=last_month
    ).count()
    notifications_last_week = NotificationLog.objects.filter(
        order__organization=org, timestamp__date__gte=last_week
    ).count()

    # --- Trend Calculator ---
    def calculate_trend(current_value, previous_value):
        if previous_value == 0:
            return 0
        return round(((current_value - previous_value) / previous_value) * 100)

    active_trend = calculate_trend(active_orders, active_orders_last_week)
    delivered_trend = calculate_trend(delivered_today, delivered_yesterday)
    customers_trend = calculate_trend(total_customers, total_customers_last_month)
    notifications_trend = calculate_trend(notifications_sent, notifications_last_week)

    # --- Orders Query with Search & Pagination ---
    orders_qs = Order.objects.filter(organization=org).select_related("customer", "status").order_by("-created_at")
    if query:
        orders_qs = orders_qs.filter(
            Q(order_number__icontains=query) |
            Q(title__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(customer__email__icontains=query)
        )
    paginator = Paginator(orders_qs, 25)
    page_number = request.GET.get("page")
    orders_qs = paginator.get_page(page_number)

    # --- Notification Feed ---
    notification_feed = NotificationLog.objects.filter(
        order__organization=org
    ).select_related("order").order_by("-timestamp")[:10]

    recent_events = []
    for log in notification_feed:
        status = log.order.status
        recent_events.append({
            "title": status.name if status else "No Stage",
            "message": f"Order #{log.order.order_number} moved to {status.name if status else 'No Stage'}",
            "channel": log.channel,
            "timestamp": log.timestamp,
            "order": log.order,
            "status_color": getattr(status, "color", "slate") if status else "slate",
            "status_name": status.name if status else "No Stage",
        })

    # --- Pipeline Counts ---
    stages = WorkflowStage.objects.filter(organization=org).order_by("position")
    status_counts = (
        Order.objects
        .filter(organization=org)
        .values("status")
        .annotate(count=Count("id"))
    )
    status_counts_dict = {s["status"]: s["count"] for s in status_counts if s["status"] is not None}
    total_orders = Order.objects.filter(organization=org).count()

    pipeline = []
    for stage in stages:
        count = status_counts_dict.get(stage.id, 0)
        percent = round((count / total_orders) * 100, 1) if total_orders else 0
        pipeline.append({
            "id": stage.id,
            "name": stage.name,
            "count": count,
            "percent": percent,
            "color": stage.color,
            "is_final": stage.is_final,
        })

    # Include orders without stage
    none_count = Order.objects.filter(organization=org, status__isnull=True).count()
    if none_count > 0:
        percent = round((none_count / total_orders) * 100, 1) if total_orders else 0
        pipeline.append({
            "id": None,
            "name": "No Stage",
            "count": none_count,
            "percent": percent,
            "color": "slate",
            "is_final": False,
        })

    context = {
        "organization": org,
        "active_orders": active_orders,
        "delivered_today": delivered_today,
        "total_customers": total_customers,
        "notifications_sent": notifications_sent,
        "recent_orders": orders_qs,
        "notification_feed": notification_feed,
        "recent_events": recent_events,
        "pipeline": pipeline,
        "active_trend": active_trend,
        "active_trend_abs": abs(active_trend),
        "delivered_trend": delivered_trend,
        "delivered_trend_abs": abs(delivered_trend),
        "customers_trend": customers_trend,
        "customers_trend_abs": abs(customers_trend),
        "notifications_trend": notifications_trend,
        "notifications_trend_abs": abs(notifications_trend),
        "query": query,
    }

    return render(request, "dashboard/dashboard.html", context)


# --- AJAX endpoint for live feed ---
@login_required
def notification_feed_api(request):
    org = request.user.organization
    notifications = NotificationLog.objects.filter(order__organization=org).select_related("order").order_by("-timestamp")[:10]
    data = []
    for n in notifications:
        order = n.order
        status = order.status

        data.append({
            "id": n.id,
            "order_number": order.order_number,
            "channel": n.channel,
            "message": f"Order #{order.order_number} moved to {status.name if status else 'No Stage'}",
            "timestamp": n.timestamp.isoformat(),
            "status_name": status.name if status else "No Stage",
            "status_color": getattr(status, "color", "slate") if status else "slate",
        })
    return JsonResponse({"notifications": data})


# --- Retry Failed Notification ---
@login_required
def retry_notification(request, notification_id):
    n = get_object_or_404(NotificationLog, id=notification_id)
    if n.status == "failed":
        dispatch_order_notification(
            n.order,
            f"Order #{n.order.order_number} update",
            channels=[n.channel]
        )
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "skipped"})