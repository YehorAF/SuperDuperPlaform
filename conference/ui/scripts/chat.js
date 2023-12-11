function startChat(
    serverUrl, 
    name, 
    userId, 
    chatId, 
    setInMsgBox, 
    delFromMsgBox,
    editInMsgBox
) {
    let socket = io(serverUrl, {autoConnect: false})
    const inputData = document.querySelector("#input-data")
    const msgBox = document.querySelector("#message-box")
    const editBox = document.querySelector("#edit-box")
    const sendMsgBtn = document.querySelector("#send-msg-btn")
    const editMsgBtn = document.querySelector("#edit-msg-btn")
    const delMsgBtn = document.querySelector("#del-msg-btn")

    socket.on("get_mgs", (data) => {
        setInMsgBox(data)
    })

    socket.on("edit_msg", (data) => {
        editInMsgBox(data)
    })

    socket.on("del_msg", (data) => {
        delFromMsgBox(data)
    })

    const connectRoom = () => {
        try {
            socket.connect()
            socket.emit("join", {
                "chat_id": chatId,
                "name": name
            })
        } catch(err) {
            console.log(err)
        }
    }

    const sendMsg = () => {
        const text = inputData.value
        try {
            socket.emit("send_msg", {
                "name": name,
                "user_id": userId,
                "text": text,
                "chat_id": chatId,
            })
        } catch (err) {
            console.log(err)
        }
    }

    const editMsg = () => {
        const msgId = editBox.value
        const text = msgBox.value
        try {
            socket.emit("edit_msg", {
                "msg_id": msgId,
                "user_id": userId,
                "text": text,
                "chat_id": chatId,
            })
        } catch(err) {
            console.log(err)
        }
    }

    const delMsg = () => {
        const msgId = editBox.value

        try{
            socket.emit("del_msg", {
                "msg_id": msgId,
                "chat_id": chatId
            })
            document.querySelector(`#${chatId}-${msgId}`).remove()
        } catch (err) {
            console.error("Try delete message: ", err)
        }
    }

    sendMsgBtn.addEventListener("click", () => sendMsg())
    editMsgBtn.addEventListener("click", () => editMsg())
    delMsgBtn.addEventListener("click", () => delMsg())

    connectRoom()
}