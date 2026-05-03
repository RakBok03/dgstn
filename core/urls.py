from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import HttpResponse
from django.views.static import serve
from django.urls import re_path

YANDEX_VERIFICATION_FILENAME = "yandex_7f3ca55e413f31a8.html"


def yandex_verification(request):
    content = (settings.BASE_DIR / YANDEX_VERIFICATION_FILENAME).read_text(encoding="utf-8")
    return HttpResponse(content, content_type="text/html; charset=UTF-8")


urlpatterns = [
    path(YANDEX_VERIFICATION_FILENAME, yandex_verification, name="yandex_verification"),
    path('admin/', admin.site.urls),
    path('', include('tours.urls')),
]

if settings.SERVE_MEDIA_VIA_DJANGO:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
