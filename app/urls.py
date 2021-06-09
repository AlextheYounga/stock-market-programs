"""hazlitt URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoapp.com/en/3.1/topics/http/urls/
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
from django.urls import path
from .controller import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('vix/', views.vix, name='vix.index'),
    path('vix/<str:ticker>/', views.vix, name='vix.show'),
    path('correlations', views.correlations, name='correlations.index'),
    path('correlations/<str:ticker>/', views.correlations, name='correlations.show'),
    path('pricedingold', views.pricedingold, name='gold.index'),
    path('pricedingold/<str:ticker>/', views.pricedingold, name='gold.show'),
    path('news', views.news, name='news.index'),
    path('hurst', views.hurst, name='hurst.index'),
    path('hurst/<str:ticker>/', views.hurst, name='hurst.show'),    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'app.controller.views.handler404'
handler500 = 'app.controller.views.handler500'
