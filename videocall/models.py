from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

#Model for Storing Channel Name of Participants   
class Participant(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    channelname = models.CharField(max_length = 250)
    
    def __str__(self):
        return self.user.username

#Model for Chat Room
class ChatRoom(models.Model):
    roomid = models.CharField(max_length=250,primary_key=True)
    admin = models.ForeignKey(User,on_delete=models.CASCADE)
    participants = models.ManyToManyField(Participant,related_name="participant",blank=True)
    
    def __str__(self):
        return self.roomid
 
    