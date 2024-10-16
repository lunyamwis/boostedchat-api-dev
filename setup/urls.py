"""setup URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "BoostedChat Admin"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),  # new
    path("v1/authentication/", include("authentication.urls")),
    path("v1/instagram/", include("instagram.urls")),
    path("v1/sales/", include("sales_rep.urls")),
    path("v1/leads/", include("leads.urls")),
    path("v1/logs/", include("audittrails.urls")),
    path("v1/dialogflow/", include("dialogflow.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
