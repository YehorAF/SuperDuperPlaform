// обробляє PeerToPeer з'єднання:
// - усе автоматично
// вдосконалення: 
// - додати події при від'єднанні користувача
// - додати localStorage
// - додати кейси в handleSignalingData
// - serverUrl - шлях для під'єднання сокета до сервера
// - localStream - stream, отриманий від користувача, який транслює відео з вебкамери
// - userId - виокремлює користувача, але надалі це все буде через хедери
// - roomId - виокремлює кімнату, але далі буде через хедери
// - createVideo - функція, яка налаштовує вигляд віконка трансляції
function startConference(serverUrl, localStream, userId, roomId, createVideo) {
    // налаштування серверів
    const PC_CONFIG = {
        iceServers: [
            {
                urls: "stun:openrelay.metered.ca:80",
            },
            {
                urls: "turn:openrelay.metered.ca:80",
                username: "openrelayproject",
                credential: "openrelayproject",
            },
            {
                urls: "turn:openrelay.metered.ca:443",
                username: "openrelayproject",
                credential: "openrelayproject",
            },
            {
                urls: "turn:openrelay.metered.ca:443?transport=tcp",
                username: "openrelayproject",
                credential: "openrelayproject",
            },
        ],
    };

    // сокет для сигналінгу сервера (конект тільки за деякими умовами)
    let socket = io(serverUrl, { autoConnect: false });

    // виклик при надходженні даних
    socket.on("data", (data) => {
        console.log("Data received: ", data);
        handleSignalingData(data);
    });

    // виклик при новому запиті на P2P з'єднання
    socket.on("ready", (msg) => {
        console.log("Ready");
        peers[msg.sid] = createPeerConnection();
        sendOffer(msg.sid);
        addPendingCandidates(msg.sid);
    });

    // функція для передачі даних
    const sendData = (data) => {
        socket.emit("data", data);
    };

    let peers = {}
    let pendingCandidates = {}

    // перевірка доступу до камери
    const checkStream = () => {
        if (!localStream) {
            throw "stream is null"
        } else {
            console.log("start connection");
            socket.connect();
            socket.emit("join", {"user_id": userId, "room": roomId});
        }
    };

    // створення й налаштування P2P з'єднання
    const createPeerConnection = () => {
        const pc = new RTCPeerConnection(PC_CONFIG);
        pc.onicecandidate = onIceCandidate;
        pc.onaddstream = onAddStream;
        pc.addStream(localStream);
        console.log("PeerConnection created");
        return pc;
    };

    // відправити пропозицію на P2P
    const sendOffer = (sid) => {
        console.log("Send offer");
        peers[sid].createOffer().then(
            (sdp) => setAndSendLocalDescription(sid, sdp),
            (error) => {
                console.error("Send offer failed: ", error);
            }
        );
    };

    // відправити відповідь на пропозицію P2P
    const sendAnswer = (sid) => {
        console.log("Send answer");
        peers[sid].createAnswer().then(
            (sdp) => setAndSendLocalDescription(sid, sdp),
            (error) => {
                console.error("Send answer failed: ", error);
            }
        );
    };

    // поміняти опис з'єднання 
    const setAndSendLocalDescription = (sid, sessionDescription) => {
        peers[sid].setLocalDescription(sessionDescription);
        console.log("Local description set");
        sendData({ sid, room: roomId, user: userId, type: sessionDescription.type, sdp: sessionDescription.sdp });
    };

    // при змінні даних кандидати
    const onIceCandidate = (event) => {
        if (event.candidate) {
            console.log("ICE candidate");
            sendData({
                type: "candidate",
                candidate: event.candidate,
                room: roomId,
                user: userId
            });
        }
    };

    // додати новий stream
    const onAddStream = (event) => {
        console.log("Add stream");
        createVideo(event.stream);
    };

    // додавання новго кандидата
    const addPendingCandidates = (sid) => {
        if (sid in pendingCandidates) {
            pendingCandidates[sid].forEach(candidate => {
                peers[sid].addIceCandidate(new RTCIceCandidate(candidate))
            });
        }
    }

    // хз, як описати, але тут відбувається вся "магія"
    // щодо відправки даних, додавання нових трансляцій тощо
    const handleSignalingData = (data) => {
        console.log(data)
        const sid = data.sid;
        delete data.sid;
        switch (data.type) {
            case "offer":
                peers[sid] = createPeerConnection();
                peers[sid].setRemoteDescription(new RTCSessionDescription(data));
                sendAnswer(sid);
                addPendingCandidates(sid);
                break;
            case "answer":
                peers[sid].setRemoteDescription(new RTCSessionDescription(data));
                break;
            case "candidate":
                if (sid in peers) {
                    peers[sid].addIceCandidate(new RTCIceCandidate(data.candidate));
                } else {
                    if (!(sid in pendingCandidates)) {
                        pendingCandidates[sid] = [];
                    }
                    pendingCandidates[sid].push(data.candidate)
                }
                break;
        }
    };

    // перевірка трансляції для початку алгоритму
    checkStream();
}