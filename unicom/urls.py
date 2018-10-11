"""unicom URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views
from django.urls import include, path

from accounts.views import UnicomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', UnicomLoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), {'next_page': '/'}, name='logout'),

    path('api/customers/', include('partners.urls')),
    path('api/offers/', include('lenders.urls')),
    path('api/applications/', include('applications.urls')),


] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
