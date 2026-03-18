from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_organization, name='register_organization'),
    path('invite/', views.invite_staff, name='invite_staff'),
    path('invitation/<str:token>/', views.accept_invitation, name='accept_invitation'),
    path('members/', views.organization_members, name='organization_members'),
]
