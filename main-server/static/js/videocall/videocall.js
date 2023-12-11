//Initialisation of variables
var username = JSON.parse(document.getElementById('username').textContent);
const roomid = JSON.parse(document.getElementById('room-id').textContent);
const room = document.getElementById('room');
const videos = document.getElementById('videos');
const ready_room = document.getElementById("ready-room");
const return_room = document.getElementById('return-room');
const readyroomlocalVideo = document.getElementById("localVideo");
const joinedlocalVideo = document.getElementById("localVideo-joined");
const roomnotfound = document.getElementById('roomnotfound');
var local_Stream = new MediaStream();
var pc = null; //PeerConnection
var websocket = null; ///WebSocket
var peerConnectionends = [] ; //list of peerconnection ends

if(roomnotfound.style.display === 'block'){
    stopstreamaccess();
}

//Stopping streamaccess after leave room or room not found
function stopstreamaccess()
{
    local_Stream.getTracks().forEach(track => {
        track.stop();
    });
    readyroomlocalVideo.srcObject = null;
    local_Stream = null;
}

var valid = false;

function checkroom(callback)
{
    $.ajax({
        type:"GET",
        url:(window.location.origin + "/checkroom/"+roomid),
        success: function(result){
            if(result.valid){
                document.getElementById('Join-Room').removeAttribute('disabled');
                console.log("Valid");
                callback();
            }        
            else
            {
                console.log("Invalid");
                stopstreamaccess();
                ready_room.style.display = 'none';
                document.getElementById('roomnotfound').style.display = 'block';
            }    
        },
        error:function(result){
            console.error(result);
        }
    })
}
checkroom(validroom);

function validroom()
{
    // alert("Entered");
    function getRowsAndColsLS(nvideos){
        return (nvideos === 1)? [1,1]:
               (nvideos === 2)? [1,2]:
               (nvideos === 3)? [1,3]:
               (nvideos === 4)? [2,2]:
               (nvideos === 5||nvideos === 6)? [2,3]:
               (nvideos === 7||nvideos === 8)? [2,4]:
               (nvideos === 9)? [3,3]:
               (nvideos === 10)? [4,3]:
               (nvideos === 11||nvideos === 12)? [3,4]:
               (nvideos >= 13) ? [4,4] : null;
    }
    
    function getRowsAndColsSS(nvideos){
        return (nvideos === 1)? [1,1]:
               (nvideos === 2)? [2,1]:
               (nvideos === 3||nvideos === 4)? [2,2]:
               (nvideos === 5||nvideos === 6)? [3,2]:
               (nvideos >= 7)? [4,2]: null; 
    }
    //Set the CSS of videos
    function setVideoCSS()
    {
        const videoframes = document.querySelectorAll('.grid-item');
        const nvideos = videoframes.length;
        var screen=0;
        if(window.innerWidth <= 430){screen = 1;}

        let dims;
        if(!screen){ //Large Screen
            dims = getRowsAndColsLS(nvideos);
        }
        else
        {
            dims = getRowsAndColsSS(nvideos);
        }
        const width = 100/dims[1];
        const len = 100/dims[0];
        const lastvideowidth = (dims[0]*dims[1] - nvideos + 1);
        const csselem = document.querySelector('.grid-container');
        csselem.style.setProperty('grid-template-columns','repeat('+dims[1]+','+width+'%)');
        csselem.style.setProperty('grid-template-rows','repeat('+dims[0]+','+len+'%)');
        videoframes[nvideos - 1].style.setProperty('grid-column','auto / span '+lastvideowidth);
    }
    
    //Adding resize eventlistener to make appropriate UI changes
    window.onresize = setVideoCSS;
    
    //Set up the getUserMedia
    //Constraints to the localstream
    let constraints = {
        'video':true,
        'audio':{
            'echoCancellation': true
        }
    }
    
    function beReady(){
        //console.log("Got the settings");
        navigator.mediaDevices.getUserMedia(constraints)
        .then(stream => {
            console.log('Got MediaStream: ',stream);
            local_Stream = stream;
            const localstream = document.querySelector("video#localVideo");
            localstream.srcObject = stream;
            roomsettings();
        })
        .catch(error => {
            console.log('Error accessing media devices.',error);
        })
    }
    beReady();
    
    //Settings of mediastream in room
    function roomsettings()
    {
        const audio_ready = document.querySelectorAll(".audio-toggle");
        const video_ready = document.querySelectorAll(".video-toggle");

        audio_ready.forEach(btn => {
            btn.onclick = () => {
                //localvideo.muted = !localvideo.muted;
                local_Stream.getAudioTracks().forEach(track => {
                    track.enabled = !track.enabled;
                    if(!track.enabled)
                    {
                        audio_ready.forEach(btn_ => {
                            btn_.innerHTML = '<i class="bi bi-mic-mute-fill"></i>';
                            btn_.style.backgroundColor = 'red';
                        });
                    }
                    else{
                        audio_ready.forEach(btn_ => {
                            btn_.innerHTML = '<i class="bi bi-mic-fill"></i>';
                            btn_.style.backgroundColor = '#63adf1';
                        });
                    }
                })
                     
            }
        });
        
        video_ready.forEach(btn => {
            btn.onclick = () => {
                local_Stream.getVideoTracks().forEach(track => {
                    track.enabled = !track.enabled;
                    if(!track.enabled)
                    {
                        video_ready.forEach(btn_ => {
                            btn_.innerHTML = '<i class="bi bi-camera-video-off-fill"></i>';
                            btn_.style.backgroundColor = 'red';
                        });
                    }
                    else{
                        video_ready.forEach(btn_ => {
                            btn_.innerHTML = '<i class="bi bi-camera-video-fill"></i>';
                            btn_.style.backgroundColor = '#63adf1';
                        });
                    }
                })
            }
        })
    }
    
    
    function activateroom()
    {
        ready_room.style.display="none";
        room.style.display="flex";
        joinedlocalVideo.srcObject = local_Stream
        readyroomlocalVideo.srcObject = null;
    
        //Leave meeting button activated after peerconnection is initiated 
    }
    
    //Leave Room Button Handler
    document.getElementById('leave-room').onclick = () => {
        websocket.close();
        peerConnectionends.forEach(end => {
            end.close();
            end = null;
            delete end;
        })
        peerConnectionends = null;
        delete peerConnectionends;
    }
    
    //Function for Sending signal to websocket
    function sendSignal(type,data)
    {
        websocket.send(JSON.stringify({
            user:username,
            type:type,
            data:data
        }));
        //Channelname is addded later
    }
    
    function handleWebSocketMessage(event)
    {
        message = JSON.parse(event.data);
        //console.log("Message",message);
        var type = message.type;
        var sender = message.user;
        var senderchannelname = message.data.receiverchannelname;
        
        //console.log(sender," ",type," ",senderchannelname);
        //if the sender is currentuser then do nothing
        if(sender === username){
            return;
        }
    
        if(type === 'accepted')
        {
            username = message.user;
            //console.log("Successfully accepted and changed username",username);
            sendSignal('new-participant',{});
            return;
        }
    
        if(type === 'new-participant')
        {
            console.log("New Participant");
            pc=null;
            pc = OfferRTCPeerConnection(sender,senderchannelname);
            return;
        }
        if(type === 'offer')
        {
            console.log("New Offer");
            pc = AnswerRTCPeerConnection(sender,senderchannelname,message.data.offer);
            return;
        }
        if(type === 'answer' && pc!=null)
        {   
            console.log("New Answer");
            receiveAnswer(pc,message.data.answer);
            return;
        }
        if(type === 'ICECandidate' && pc!==null)
        {
            //console.log("New ICECandidate");
            receiveICECandidates(pc,message.data.ICECandidate);
            return;
        }
    }
    
    //On clicking join now create websocket connection
    document.getElementById("Join-Room").onclick = () => {
        // joinroom();
        
        //Setting up the websocket for django-channels
        var protocol = "ws://";
        if(window.location.protocol === "https"){protocol = "wss://";}
    
        //Websocket Constructor
        websocket = new WebSocket(
            protocol+
            window.location.host+
            '/'+
            roomid+
            '/'
        );
        
        if(websocket === null){return;}
        //Inform all in the room that a new participant has arrived
        websocket.onopen = () => {
            //console.log("Socket Connection Opened");
            //sendSignal('new-participant',{});
            activateroom();
        }
        websocket.onclose = () => {
            console.log("Socket Connection closed");
            room.style.display = "none";
            return_room.style.display="block";
            joinedlocalVideo.srcObject = null;
            
            //stop the stream access here
            stopstreamaccess();
        }
        websocket.onmessage = handleWebSocketMessage;
    }
    
    //Start a peerconnection end and send offer to remotePeer
    function OfferRTCPeerConnection(sender,receiverchannelname)
    {
        //Configuration of STUN AND TURN Servers
        const configuration = {'iceServers': [{'urls': 'stun:stun.l.google.com:19302'}]}
        const peerConnection = new RTCPeerConnection(configuration);
        peerConnectionends.push(peerConnection);
    
        addMediaTracks(peerConnection);
    
        //Set the onicecandidate event
        setIceCandidateEvent(peerConnection,receiverchannelname);
        
        //Create video element for remote Peer
        var remoteVideo = createRemoteVideo(sender);
        setRemoteTracks(remoteVideo,peerConnection);
    
        //set the oniceconnectionstatechange event
        setICEConnectionStateChange(peerConnection,remoteVideo.id);
    
        //CreateOffer
        createoffer(peerConnection,receiverchannelname);
        
        //console.log("Peer Connection: ",peerConnection);
        return peerConnection;
    }
    
    //Start a peerconnection end and send answer to remotePeer
    function AnswerRTCPeerConnection(sender,receiverchannelname,offer)
    {
        //Configuration of STUN AND TURN Servers
        const configuration = {'iceServers': [{'urls': 'stun:stun.l.google.com:19302'}]}
        const peerConnection = new RTCPeerConnection(configuration);
        peerConnectionends.push(peerConnection);
    
        addMediaTracks(peerConnection);
    
        //Set the onicecandidate event
        setIceCandidateEvent(peerConnection,receiverchannelname);
        
        //Create video element for remote Peer
        var remoteVideo = createRemoteVideo(sender);
        setRemoteTracks(remoteVideo,peerConnection);
    
        //set the oniceconnectionstatechange event
        setICEConnectionStateChange(peerConnection,remoteVideo.id);
    
        //CreateAnswer
        createanswer(peerConnection,offer,receiverchannelname);
        
        //console.log("Peer Connection: ",peerConnection);
        return peerConnection;
    }
    
    //Add all the audio and video tracks to be sent 
    function addMediaTracks(peerConnection){
        local_Stream.getTracks().forEach(track => {
            peerConnection.addTrack(track);
        });
    }
    
    //Trickle ICE (Send ICE Candidates to remote peer)
    function setIceCandidateEvent(peerConnection,receiverchannelname)
    {
        //Setting onicecandidate
        //Listen for local ICE candidates on the local RTCPeerConnection
        //Send IceCandidates to peer
        peerConnection.onicecandidate = (event) => {
            if(event.candidate){
                //console.log("Sending ICE Candidate",event.candidate);
                sendSignal('ICECandidate',{
                    'ICECandidate':event.candidate,
                    'receiverchannelname':receiverchannelname
                });   
            }
            else{
                console.log("All ICE candidates have been sent!!");
            }
        }
    }
    
    //Handling Connection State Change of a peer
    function setICEConnectionStateChange(peerConnection,remoteVideo)
    {
        console.log("Set iceconnection statechange event");
        peerConnection.oniceconnectionstatechange = (event) => {
            var iceConnectionState = peerConnection.iceConnectionState;
            if(iceConnectionState === 'disconnected'||
               iceConnectionState === 'failed' ||
               iceConnectionState === 'closed'
            )
            {
                if(iceConnectionState!== 'closed')
                {
                    peerConnection.close();
                    peerConnection = null;
                    delete peerConnection;
                    pc=null;
                }
                removeRemoteVideo(remoteVideo);
            }
        }
    }
    
    //Receive ICE Candidates from peer
    async function receiveICECandidates(peerConnection,iceCandidate)
    {
        if(iceCandidate)
        {
            try{
                await peerConnection.addIceCandidate(iceCandidate);
            }
            catch(error){
                console.log('Error adding received ice candidate',error);
            }
        }
    }
    
    //Create video element of peer
    function createRemoteVideo(sender)
    {
        //Create the div of the remote video
        divofRemoteVideo = document.createElement('div');
        divofRemoteVideo.setAttribute("class","videotrack grid-item");
        //RemoteVideo element
        remoteVideo = document.createElement('video');
        remoteVideo.id = (sender+'Video');
        remoteVideo.autoplay = true;
        //Append the video to the div
        divofRemoteVideo.appendChild(remoteVideo);
        //Add this to the ROOM
        videos.appendChild(divofRemoteVideo);
    
        //Change the CSS of the videos
        setVideoCSS();
    
        return remoteVideo;
    }
    
    //Remove through Signalling Server
    function removeRemoteVideo(remoteVideoID)
    {
        console.log("Peer Video Removed");
        document.getElementById(remoteVideoID).parentNode.remove();
        setVideoCSS();
    }
    
    //On TrackEvent Handler
    function setRemoteTracks(remoteVideo,peerConnection)
    {
        var remoteStream = new MediaStream();
        remoteVideo.srcObject = remoteStream;
        peerConnection.ontrack =async (event) =>{
            remoteStream.addTrack(event.track,remoteStream);
        }
    }
    
    //Create and send offer to remote peer
    function createoffer(peerConnection,receiverchannelname)
    {
        peerConnection.createOffer()
        .then(offer => {
            peerConnection.setLocalDescription(offer)
            .then(() => {
                console.log("Sending offer");
                sendSignal('offer',{
                    'offer':offer,
                    'receiverchannelname':receiverchannelname
                });
            })
            .catch(error => {
                console.log("Error in setLocalDesc: ",error);
            })
        })
        .catch(error => {
            console.log("Error in creating offer",error);
        })
    }
    
    //Create and send answer to remote peer
    function createanswer(peerConnection,offer,receiverchannelname)
    {
        if(offer)
        {
            peerConnection.setRemoteDescription(new RTCSessionDescription(offer))
            .then(() => {
                peerConnection.createAnswer()
                .then(answer => {
                    peerConnection.setLocalDescription(answer)
                    .then(() => {
                        console.log("Sending answer");
                        sendSignal('answer',{
                            'answer':answer,
                            'receiverchannelname':receiverchannelname
                        })
                    })
                })
            })
        }   
    }
    
    //Recieve answer from remote peer
    async function receiveAnswer(peerConnection,answer)
    {
        if(answer)
        {
            const remoteDesc = new RTCSessionDescription(answer);
            await peerConnection.setRemoteDescription(remoteDesc);
            //console.log("Remote desc done");
        }
    }
    
    /*
    //Fetch an array of devices of a certain type
    function getConnectedDevices(type,callback){
        navigator.mediaDevices.enumerateDevices()
        .then(devices => {
            const filtered = devices.filter(device => device.kind === type);
            callback(filtered);
        })
        .catch(error => {
            console.log("Error in getting devices of type : ",type);
        })
    }
    
    function refreshdevices(devices){
    
        let cameras = document.querySelector('select#availableCameras');
        let microphones = document.querySelector('select#availableMicrophones');
        let speakers = document.querySelector('select#availableSpeakers');
        
        cameras.innerHTML = '';
        microphones.innerHTML = '';
        speakers.innerHTML = '';
    
        devices.map(device => {
            const deviceOption = document.createElement("option");
            deviceOption.label = device.kind;
            deviceOption.text = device.label;
            deviceOption.value = device.deviceId;
            return deviceOption;
        })
        .forEach(deviceOption => {
            
            if (deviceOption.label === 'videoinput'){
                cameras.add(deviceOption);
            }
            if (deviceOption.label === 'audioinput'){
                microphones.add(deviceOption);
            }
            if (deviceOption.label === 'audiooutput'){
                speakers.add(deviceOption);
            }
    
        });
    }
    
    //Listen for changes to media devices and update the list accordingly
    navigator.mediaDevices.ondevicechange = () => {
        getConnectedDevices('audioinput',refreshdevices);
        getConnectedDevices('audiooutput',refreshdevices);
        getConnectedDevices('videoinput',refreshdevices);
    }
    */
//    alert("Exit");
}

