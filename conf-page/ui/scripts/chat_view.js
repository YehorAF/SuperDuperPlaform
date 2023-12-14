window.addEventListener("DOMContentLoaded", () => {
    const msgBox = document.querySelector("#msg-box")

    const setInMsgBox = (data) => {
        const sid = data.sid
        const userId = data["user_id"]
        const chatId = data["chat_id"]
        const msgId = data["msg_id"]
        const name = data["name"]
        const text = data["text"]
        const timestamp = data["timestamp"]
        const datetime = new Date(timestamp * 1000)
        const date = datetime.toLocaleDateString()
        const time = datetime.toTimeString()

        const header = document.createElement("header")
        header.className = "msg-header"
        header.textContent = `${name}\t${date}-${time}`

        const content = document.createElement("span")
        content.className = "msg-content"
        content.textContent = text

        const msg = document.createElement("div")
        msg.className = "message"
        msg.id = `#${chatId}-${msgId}`
        msg.appendChild(header)
        msg.appendChild(content)

        msgBox.appendChild(msg)
    }

    const editInMsgBox = (data) => {
        const sid = data.sid
        const chatId = data["chat_id"]
        const msgId = data["msg_id"]
        const text = data["text"]
        document.querySelector(`#${chatId}-${msgId} span.msg-content`).textContent = text
    }

    const delFromMsgBox = (data) => {
        const sid = data.sid
        const chatId = data["chat_id"]
        const msgId = data["msg_id"]
        document.querySelector(`#${chatId}-${msgId} span.msg-content`).remove()
    }

    const url = `${window.location.origin}/conference_socks/chat`

    startChat(url, "", "", "", setInMsgBox, delFromMsgBox, editInMsgBox)
})