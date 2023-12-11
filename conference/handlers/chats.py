from aiohttp import web
from aiohttp_cors import mixin
import aiohttp_jinja2
import bson
from datetime import datetime
import socketio
import logging

from tools.database import Database
from tools.exceptions import UniqueDataError, MissingUserError, DBResultError
from tools.wrapped_funcs import to_inst, parse_content


class ChatNamespace(socketio.AsyncNamespace):
    def __init__(self, database: Database, namespace=None):
        super().__init__(namespace)
        self._database = database


    async def on_connect(self, sid, *args, **kwargs):
        pass


    async def on_disconnect(self, sid):
        pass


    async def on_join(self, sid, data: dict):
        chat_id = data["chat_id"]
        chat_id_bson = bson.ObjectId(chat_id)
        name = data["name"]
        _, count = await self._database.channel_chats.get(
            {"_id": chat_id_bson}, {"_id": 1})
        if count < 1:
            return
        await self.enter_room(sid, chat_id)


    async def on_get_msg(self, sid, data: dict):
        pass


    async def on_send_msg(self, sid, data: dict):
        name = data.get("name")
        text = data.get("text")
        # files = data.get("files")
        chat_id = data["chat_id"]
        user_id = data["user_id"]
        user_id_bson = bson.ObjectId(user_id)
        timestamp = datetime.timestamp(datetime.now())
        upd_data = {
            "user_id": user_id_bson,
            "chat_id": bson.ObjectId(chat_id),
            "text": text,
            # "files": files,
            "timestamp": timestamp
        }
        res = await self._database.channel_chat_msgs.add_one(upd_data)
        if not res or not res.inserted_id:
            return
        await self.emit(event="get_msg", data={
            "msg_id": str(res.inserted_id),
            "user_id": user_id,
            "sid": sid,
            "name": name,
            "text": text,
            # "files": files,
            "chat_id": chat_id,
            "timestamp": timestamp
        }, room=chat_id)


    async def on_edit_msg(self, sid, data: dict):
        keys = ["text"] #, "files"]
        upd_data = {}
        for k in keys:
            v = data.get(k)
            if v:
                upd_data.update({k: v})
        if not upd_data:
            return
        chat_id = data["chat_id"]
        msg_id = data["msg_id"]
        res = await self._database.channel_chat_msgs.update({
            "sid": sid,
            "chat_id": bson.ObjectId(chat_id),
            "_id": bson.ObjectId(msg_id)
        }, upd_data)
        if res.modified_count < 1:
            return
        await self.emit(event="edit_msg", data={
                "msg_id": msg_id,
                "sid": sid,
                "chat_id": chat_id
        } | upd_data, room=chat_id, skip_sid=sid)


    async def on_del_msg(self, sid, data: dict):
        chat_id = data["chat_id"]
        msg_id = data["msg_id"]
        res = await self._database.channel_chat_msgs.delete({
            "sid": sid,
            "chat_id": bson.ObjectId(chat_id),
            "msg_id": bson.ObjectId(msg_id)
        })
        if res.deleted_count < 1:
            return
        await self.emit(event="del_msg", data={
            "sid": sid,
            "msg_id": msg_id,
            "chat_id": chat_id
        }, room=chat_id, skip_sid=sid)


class ChatsView(web.View, mixin.CorsViewMixin):
    async def get(self):
        request = self.request
        database: Database = request["database"]
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        channel_id = bson.ObjectId(request.match_info["channel_id"])
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        _, count = await database.channels.get(
            {"_id": channel_id, "conference_id": conference_id})
        if count < 1:
            raise ValueError("not such channel")
        _, count = await database.conference_members.get({
            "user_id": user_id, 
            "conference_id": conference_id,
            "status": {"$not": "blocked"}
        }, {"_id": 1})
        if count < 1:
            raise MissingUserError("you haven't permission to get chats")
        limit = to_inst(self.request.get("limit"), int) or 10
        ind = to_inst(self.request.get("ind"), int) or 0 
        end = ind + limit
        chats, count = await database.channel_chats.get(
            {"channel_id": channel_id})
        if count < 1:
            raise ValueError("there aren't chats")
        chats = chats[ind:end]
        for chat in chats:
            chat.update({"_id": str(chat["_id"])})
        response_data = {
            "begin_ind": ind,
            "end_ind": end,
            "limit": limit,
            "count": count,
            "chats": chats
        }
        return response_data, {}, "getting chats was successful"
        

    async def post(self):
        request = self.request
        database: Database = request["database"]
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        channel_id = bson.ObjectId(request.match_info["channel_id"])
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        _, count = await database.channels.get(
            {"_id": channel_id, "conference_id": conference_id}, {"_id": 1})
        if count < 1:
            raise ValueError("not such channel")
        _, count = await database.conference_members.get({
            "user_id": user_id, 
            "conference_id": conference_id,
            "status": {"$in": ["admin", "owner"]}
        }, {"_id": 1})
        if count < 1:
            raise MissingUserError("you haven't permission to create chats")
        name = request["name"]
        info = request["info"]
        res = await database.channel_chats.add_one({
            "channel_id": channel_id,
            "conference_id": conference_id,
            "name": name, "info": info
        })
        if not res or not res.inserted_id:
            raise DBResultError("cannot add channel chat")
        return {}, {}, "channel chat was added"
        

class ChatView(web.View, mixin.CorsViewMixin):
    async def get(self):
        request = self.request
        database: Database = request["database"]
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        # channel_id = bson.ObjectId(request.match_info["channel_id"])
        chat_id = bson.ObjectId(request.match_info["chat_id"])
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        _, count = await database.conference_members.get({
            "user_id": user_id, 
            "conference_id": conference_id,
            "status": {"$not": "blocked"}
        }, {"_id": 1})
        if count < 1:
            raise MissingUserError("you haven't permission to get chat")
        chats, count = await database.channel_chats.get(
            {"_id": chat_id, "conference_id": conference_id}, {"_id": 0})
        if count < 1:
            raise ValueError("there is no such chat")
        chat = chats
        return chat, {}, "chat was found"


    async def put(self):
        request = self.request
        database: Database = request["database"]
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        # channel_id = bson.ObjectId(request.match_info["channel_id"])
        chat_id = bson.ObjectId(request.match_info["chat_id"])
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        _, count = await database.conference_members.get({
            "user_id": user_id, 
            "conference_id": conference_id,
            "status": {"$in": ["admin", "owner"]}
        }, {"_id": 1})
        if count < 1:
            raise MissingUserError("you haven't permission to update chat")
        data = parse_content(request)
        keys = ["name", "info"]
        upd_data = {}
        for k in keys:
            v = data.get(k)
            if v:
                upd_data.update({k: v})
        res = await database.channel_chats.update(
            {"_id": chat_id, "conference_id": conference_id}, upd_data)
        if res.modified_count < 1:
            raise DBResultError("cannot update this chat")
        return {}, {}, "chat was updated"


    async def delete(self):
        request = self.request
        database: Database = request["database"]
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        channel_id = bson.ObjectId(request.match_info["channel_id"])
        chat_id = bson.ObjectId(request.match_info["chat_id"])
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        _, count = await database.conference_members.get({
            "user_id": user_id, 
            "conference_id": conference_id,
            "status": {"$in": ["admin", "owner"]}
        }, {"_id": 1})
        if count < 1:
            raise MissingUserError("you haven't permission to update chat")
        _, count = await database.channels.get(
            {"_id": channel_id, "conference_id": conference_id}, {"_id": 1})
        if count < 1:
            raise ValueError("there is not such channel")
        res = await database.channel_chat_msgs.delete({"chat_id": chat_id})
        res = await database.channel_chats.delete(
            {"_id": chat_id, "channel_id": channel_id})
        if res.deleted_count < 1:
            DBResultError(f"cannot delete chat: {chat_id}")
        return {}, {}, "chat was deleted"