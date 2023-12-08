from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from videocall.models import ChatRoom
from django.shortcuts import redirect

@login_required(redirect_field_name=None)
def HomePage(request):
    from django.shortcuts import render

    return render(request, "home2.html")


#Create a Room
@login_required
def CreateRoomLink(request):
    import uuid
    import base64
    
    if(request.method=="GET"):
        randomid = str(uuid.uuid4()) #RandomId Generator
        randomid_bytes = randomid.encode("ascii") #
        randomid_bytes = base64.b64encode(randomid_bytes)
        randomid = randomid_bytes.decode("ascii")
    
    try:
        ChatRoom.objects.create(pk = randomid,admin = request.user)
        return JsonResponse({'valid':1,'roomid':randomid},status=200)
    except Exception as e:
        print(e)
        return JsonResponse({'valid':0,'message':"Sorry!! Click Create-Room Again!!"},status=200)
    

@login_required
def CheckRoom(request,*args,**kwargs):
    room_id = kwargs.get('room_id',None)
    try:
        if(room_id and ChatRoom.objects.get(pk=room_id)):
            return JsonResponse({'valid':1},status=200)
    except:
        return JsonResponse({'valid':0},status=200)
    
    return True