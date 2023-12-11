from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.

class VideoCall(LoginRequiredMixin,TemplateView):
    template_name = "videocall/videocall2.html"
    
    