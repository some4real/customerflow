from django.contrib import admin
from .models import WorkflowStage


@admin.register(WorkflowStage)
class WorkflowStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'organization', 'created_at')
    list_filter = ('organization',)
    search_fields = ('name',)
    ordering = ('organization', 'position')

    # Hide organization field from non-superusers
    def get_exclude(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        return ('organization',)

    # Only show stages belonging to the user's organization
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        return qs.filter(organization=request.user.organization)

    # Automatically assign organization on save
    def save_model(self, request, obj, form, change):
        if not obj.organization_id:
            obj.organization = request.user.organization

        super().save_model(request, obj, form, change)