from django.contrib import admin
from .models import NotificationLog

class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('order', 'channel', 'status', 'timestamp')
    list_filter = ('channel', 'status')
    search_fields = ('order__title',)

admin.site.register(NotificationLog, NotificationLogAdmin)