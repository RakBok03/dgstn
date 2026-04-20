from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tours.urls')),
]

# Раздаем медиа-файлы всегда (и в DEBUG, и в PROD)
# Статику (STATIC_URL) здесь добавлять НЕ НУЖНО, её уже обслуживает WhiteNoise
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)