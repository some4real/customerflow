from django.contrib import admin
from .models import Customer

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'address','organization', 'created_at')
    search_fields = ('name', 'email', 'phone', 'address')

    # Only show customers for the logged-in user's organization
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organization=request.user.organization)

    # Automatically assign organization when creating a customer
    def save_model(self, request, obj, form, change):
        if not obj.organization:
            obj.organization = request.user.organization
        super().save_model(request, obj, form, change)

admin.site.register(Customer, CustomerAdmin)