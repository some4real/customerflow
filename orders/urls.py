from django.urls import path
from . import views
from .views import OrderListView, OrderCreateView, OrderDetailView, OrderUpdateView, update_order_status

app_name = "orders"

urlpatterns = [
    path("", OrderListView.as_view(), name="list"),
    path("create/", OrderCreateView.as_view(), name="create"),
    path("<int:pk>/", OrderDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", OrderUpdateView.as_view(), name="update"),
    path("update-status/", update_order_status, name="update_status"),
    path("batch-update-status/", views.batch_update_order_status, name="batch_update_status"),

]