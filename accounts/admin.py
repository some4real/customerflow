from django.contrib import admin
from .models import User, StaffInvitation


class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'get_name', 'role', 'organization', 'date_joined')
    list_filter = ('role', 'organization', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')
    
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email
    get_name.short_description = 'Name'


class InvitationStatusFilter(admin.SimpleListFilter):
    title = 'Invitation Status'
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return [
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'pending':
            return queryset.filter(accepted_at__isnull=True)
        if self.value() == 'accepted':
            return queryset.filter(accepted_at__isnull=False)


class StaffInvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'organization', 'get_status', 'created_at', 'created_by')
    list_filter = (InvitationStatusFilter, 'organization', 'created_at')
    search_fields = ('email', 'organization__name')
    readonly_fields = ('token', 'created_at', 'accepted_at')
    
    def get_status(self, obj):
        return 'Accepted' if obj.accepted_at else 'Pending'
    get_status.short_description = 'Status'


admin.site.register(User, UserAdmin)
admin.site.register(StaffInvitation, StaffInvitationAdmin)