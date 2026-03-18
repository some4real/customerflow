from django.urls import path
from . import views
from .views import landing_view, dashboard_view
from django.contrib.auth.views import LogoutView

app_name = "dashboard"

urlpatterns = [

    path("", landing_view, name="landing"),
    path("logout/", LogoutView.as_view(next_page="dashboard:landing"), name="logout",),
    path("dashboard/", dashboard_view, name="home"),
    path("api/notifications/", views.notification_feed_api, name="notification_feed_api"),
    path("api/notifications/retry/<int:notification_id>/", views.retry_notification, name="retry_notification"),
]
