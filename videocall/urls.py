from django.urls import path
from . import views

app_name = 'videocall'

urlpatterns = [
    path('',views.VideoCall.as_view(),name = 'room')
]
