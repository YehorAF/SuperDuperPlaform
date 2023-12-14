window.addEventListener("DOMContentLoaded", () => {
    let localStream;
    let counter = 0;

    // отриимати трансляцію
    const getLocalStream = () => {
        navigator.mediaDevices.getUserMedia({ audio: true, video: true })
            .then((stream) => {
                console.log('Stream found');
                localStream = stream;
                createVideo(stream);
            })
            .catch(error => {
                console.error('Stream not found: ', error);
            });
    }

    // функція, яка додає в'юшки для трансляцій
    const createVideo = (stream) => {
        const videoId = `video-conf-${(counter += 1)}`;
        const video = document.createElement("video");
        video.autoplay = true;
        video.srcObject = stream;
        video.id = videoId;
        document.querySelector("#video-group").appendChild(video);

        return videoId;
    }

    // функція, яка видаляє в'юшки під трансляції (треба дописати)
    const removeVideo = (videoId) => {
        document.querySelector(`#${videoId}`).remove();
    }

    document.querySelector("#allow-media").addEventListener("click", () => {
        if (!localStream) {
            getLocalStream();
        }
    });

    document.querySelector("#connect-to-conference").addEventListener("click", () => {
        if (!localStream){
            getLocalStream();
        }
        const url = `${window.location.origin}/conference_socks/conf`;
        try{
            startConference(url, localStream, "user-id", "room-id", createVideo);
        } catch (error) {
            alert(error);
        }
    });
});