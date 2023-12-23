from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'(?P<room_id>\w+)/$',consumers.VideoCallConsumer.as_asgi()),
]