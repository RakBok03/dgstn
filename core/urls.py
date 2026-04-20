from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.static import serve # Добавь этот импорт
from django.urls import re_path # Добавь этот импорт

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tours.urls')),
    
    # Прямой проброс медиа-файлов (работает при любом DEBUG)
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]