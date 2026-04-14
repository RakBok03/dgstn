from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Должно быть тут
from django.conf.urls.static import static # И это

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tours.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

