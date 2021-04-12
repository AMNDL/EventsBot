from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.conf.urls.static import static
from Events.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('webhooks/events/', csrf_exempt(MainBotView.as_view())),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
