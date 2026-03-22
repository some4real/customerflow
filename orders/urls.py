from django.urls import path
from . import views
from .views import OrderDeleteView, OrderListView, OrderCreateView, OrderDetailView, OrderUpdateView, bulk_delete_orders, update_order_status

app_name = "orders"

urlpatterns = [
    path("", OrderListView.as_view(), name="list"),
    path("create/", OrderCreateView.as_view(), name="create"),
    path("<int:pk>/", OrderDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", OrderUpdateView.as_view(), name="update"),
    path("update-status/", update_order_status, name="update_status"),
    path("batch-update-status/", views.batch_update_status, name="batch_update_status"),
    path("delete/<int:pk>/", OrderDeleteView.as_view(), name="delete_order"),
    path("bulk-delete/", bulk_delete_orders, name="bulk_delete"),

]