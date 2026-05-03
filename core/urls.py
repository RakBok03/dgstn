from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.views.static import serve
from django.urls import re_path

YANDEX_VERIFICATION_FILENAME = "yandex_7f3ca55e413f31a8.html"
SITE_ICON_DIR = settings.BASE_DIR / "images"


def yandex_verification(request):
    content = (settings.BASE_DIR / YANDEX_VERIFICATION_FILENAME).read_text(encoding="utf-8")
    return HttpResponse(content, content_type="text/html; charset=UTF-8")


def _serve_site_icon(filename, content_type):
    path = SITE_ICON_DIR / filename
    if not path.exists():
        raise Http404
    return FileResponse(path.open("rb"), content_type=content_type)


def favicon_ico(request):
    return _serve_site_icon("favicon.ico", "image/x-icon")


def favicon_png(request):
    return _serve_site_icon("favicon-120.png", "image/png")


urlpatterns = [
    path("favicon.ico", favicon_ico, name="favicon_ico"),
    path("favicon.png", favicon_png, name="favicon_png"),
    path(YANDEX_VERIFICATION_FILENAME, yandex_verification, name="yandex_verification"),
    path('admin/', admin.site.urls),
    path('', include('tours.urls')),
]

if settings.SERVE_MEDIA_VIA_DJANGO:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
