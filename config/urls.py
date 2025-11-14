from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from mailings.views import DashboardView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", DashboardView.as_view(), name="dashboard"),
    path("users/", include(("users.urls", "users"), namespace="users")),
    path("", include(("mailings.urls", "mailings"), namespace="mailings")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
