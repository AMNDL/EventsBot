import admin_thumbnails
from django.contrib import admin
from .models import Event


@admin.register(Event)
@admin_thumbnails.thumbnail('image')
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'date', 'image_thumbnail']
    search_fields = ['date', 'title', 'event_type']
