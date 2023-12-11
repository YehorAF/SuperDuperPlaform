from django.contrib import admin
from .models import Participant,ChatRoom
from django.contrib.auth import get_user_model

# Register your models here.
admin.site.register(ChatRoom)
admin.site.register(Participant)

