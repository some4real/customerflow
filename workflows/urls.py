from django.urls import path
from .views import workflow_list, workflow_create, workflow_edit, workflow_delete
app_name = "workflows"

urlpatterns = [
    path('', workflow_list, name='list'),
    path('create/', workflow_create, name='create'),
    path('<int:pk>/edit/', workflow_edit, name='edit'),
    path('<int:pk>/delete/', workflow_delete, name='delete'),
]