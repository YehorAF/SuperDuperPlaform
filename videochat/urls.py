"""videochat URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import path,include,reverse_lazy
from . import views
from django.contrib.auth.views import (PasswordResetView
                                       ,PasswordResetDoneView,PasswordResetConfirmView)
                                    #    PasswordResetCompleteView)


urlpatterns = [
    path('',include('accounts.urls')),
    path('password_reset/',PasswordResetView.as_view(),name = 'password_reset'),
    path('password_reset_done/',PasswordResetDoneView.as_view(),name = 'password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/',PasswordResetConfirmView.as_view(success_url = reverse_lazy('accounts:login')),name = 'password_reset_confirm'),
    # path('password_reset_complete/',PasswordResetCompleteView.as_view(),name = 'password_reset_complete')
    path('admin/', admin.site.urls),
    path('createroomlink/',views.CreateRoomLink,name='createroomlink'),
    path('checkroom/<str:room_id>',views.CheckRoom,name = 'checkroom'),
    path('',views.HomePage,name = 'home'),
    path('<str:room_id>/',include('videocall.urls')),
    path('createroomlink/',views.CreateRoomLink,name='createroomlink')
]
