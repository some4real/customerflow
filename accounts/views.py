from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.contrib import messages
from organizations.models import Organization
from .models import StaffInvitation
from .forms import OrganizationRegistrationForm, StaffInvitationForm, AcceptInvitationForm

User = get_user_model()

def login_view(request):
    """Custom login view to handle authentication"""
    if request.method == 'POST':
        username = request.POST.get('username')  # Email address used as username
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.email}!')
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'accounts/login.html')

def register_organization(request):
    """Register a new organization and create admin user"""
    if request.method == 'POST':
        form = OrganizationRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create organization
                    org = Organization.objects.create(
                        name=form.cleaned_data['organization_name']
                    )
                    
                    # Create admin user
                    user = User.objects.create_user(
                        username=form.cleaned_data['email'],
                        email=form.cleaned_data['email'],
                        first_name=form.cleaned_data['admin_name'].split()[0],
                        last_name=' '.join(form.cleaned_data['admin_name'].split()[1:]) if len(form.cleaned_data['admin_name'].split()) > 1 else '',
                        password=form.cleaned_data['password'],
                        organization=org,
                        role='admin'
                    )
                    
                    # Log them in
                    login(request, user)
                    messages.success(request, f'Welcome to CustomerFlow! Your organization "{org.name}" has been created.')
                    return redirect('dashboard:home')
            except Exception as e:
                messages.error(request, f'Error creating organization: {str(e)}')
    else:
        form = OrganizationRegistrationForm()
    
    return render(request, 'accounts/register_organization.html', {'form': form})


@login_required
@require_http_methods(["GET", "POST"])
def invite_staff(request):
    """Invite staff members to the organization"""
    if request.user.role != 'admin':
        messages.error(request, 'Only admins can invite staff.')
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = StaffInvitationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                messages.warning(request, 'This user is already registered.')
            else:
                # Create invitation
                try:
                    invitation = StaffInvitation.objects.get_or_create(
                        organization=request.user.organization,
                        email=email,
                        defaults={'created_by': request.user}
                    )[0]
                    
                    # Resend if already created
                    invitation.created_by = request.user
                    invitation.save()
                    
                    messages.success(request, f'Invitation sent to {email}. They can join your organization by accepting the invitation.')
                    return redirect('accounts:invite_staff')
                except Exception as e:
                    messages.error(request, f'Error sending invitation: {str(e)}')
    else:
        form = StaffInvitationForm()
    
    # Get pending invitations
    pending_invitations = StaffInvitation.objects.filter(
        organization=request.user.organization,
        accepted_at__isnull=True
    )
    
    return render(request, 'accounts/invite_staff.html', {
        'form': form,
        'pending_invitations': pending_invitations
    })


def accept_invitation(request, token):
    """Accept staff invitation and create user account"""
    invitation = get_object_or_404(StaffInvitation, token=token)
    
    if invitation.accepted_at:
        messages.info(request, 'This invitation has already been accepted.')
        return redirect('accounts:login')
    
    if request.method == 'POST':
        form = AcceptInvitationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create user
                    user = User.objects.create_user(
                        username=invitation.email,
                        email=invitation.email,
                        first_name=form.cleaned_data['name'].split()[0],
                        last_name=' '.join(form.cleaned_data['name'].split()[1:]) if len(form.cleaned_data['name'].split()) > 1 else '',
                        password=form.cleaned_data['password'],
                        organization=invitation.organization,
                        role='staff'
                    )
                    
                    # Mark invitation as accepted
                    from django.utils import timezone
                    invitation.accepted_at = timezone.now()
                    invitation.accepted_by = user
                    invitation.save()
                    
                    # Log them in
                    login(request, user)
                    messages.success(request, f'Welcome to {invitation.organization.name}!')
                    return redirect('dashboard:home')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
    else:
        form = AcceptInvitationForm()
    
    return render(request, 'accounts/accept_invitation.html', {
        'form': form,
        'email': invitation.email,
        'organization': invitation.organization
    })


@login_required
def organization_members(request):
    """List organization members"""
    if request.user.role != 'admin':
        messages.error(request, 'Only admins can view members.')
        return redirect('dashboard:home')
    
    members = User.objects.filter(organization=request.user.organization)
    invitations = StaffInvitation.objects.filter(
        organization=request.user.organization,
        accepted_at__isnull=True
    )
    
    return render(request, 'accounts/organization_members.html', {
        'members': members,
        'pending_invitations': invitations
    })
