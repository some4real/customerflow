from django.contrib import admin
from .models import Order

class OrderAdmin(admin.ModelAdmin):
    list_display = ('title', 'customer', 'status', 'organization', 'created_at', 'updated_at')
    list_filter = ('organization', 'status')
    search_fields = ('title', 'customer__name')

    # Only show orders for the logged-in user's organization
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organization=request.user.organization)

    # Automatically assign organization when creating an order
    def save_model(self, request, obj, form, change):
        if not obj.organization:
            obj.organization = request.user.organization
        super().save_model(request, obj, form, change)

admin.site.register(Order, OrderAdmin)