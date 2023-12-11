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


class ChannelStreamHandler(socketio.AsyncNamespace):
    def __init__(self, database: Database, namespace=None):
        super().__init__(namespace)
        self._database = database


    async def on_connect(self, sid, *args, **kwargs):
        pass


    async def on_join(self, sid, data):
        channel_id = data["channel"]
        channel_id_bson = bson.ObjectId(channel_id)
        member_id = bson.ObjectId(data["member_id"])
        user_id = bson.ObjectId(data["user_id"])
        conference_id = bson.ObjectId(data["conference_id"])
        _, count = await self._database.conference_members.get({
            "_id": member_id, "user_id": user_id,
            "conference_id": conference_id, "status": {"$not": "blocked"}
        }, {"_id": 1})
        if count < 1:
            return
        _, count = await self._database.channels.get({
            "_id": channel_id_bson, "conference_id": conference_id
        }, {"_id": 1})
        if count < 1:
            return
        res = await self._database.channel_members.add_one({
            "channel_id": channel_id_bson, 
            "member_id": member_id,
            "sid": sid, 
            "timestamp": datetime.timestamp(datetime.now())
        })
        if not res or not res.inserted_id:
            return
        users, _ = await self._database.users.get({
            "_id": user_id
        }, {"name": 1, "photo": 1})
        user = users[0]
        await self.enter_room(sid, channel_id)
        await self.emit(
            event="ready",
            data={"sid": sid} | user,
            room=channel_id,
            skip_sid=sid
        )


    async def on_data(self, sid, data: dict):
        room = data.get("room")
        send_to = data.get("sid")
        data = data | {"sid": sid}
        await self.emit(
            event="data", data=data, room=(send_to or room), skip_sid=sid)
        

    async def on_disconnect(self, sid, *args, **kwargs):
        members, count = await self._database.channel_members.get(
            {"sid": sid})
        if count < 0:
            return
        member = members[0]
        room = str(member["channel_id"])
        await self.leave_room(sid, room)
        await self.emit("leave", data={"sid": sid}, room=room, skip_sid=sid)
        await self._database.channel_members.delete({"sid": sid})


class ChannelsView(web.View, mixin.CorsViewMixin):
    async def get(self):
        request = self.request
        database: Database = request["database"]
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        # member_id = bson.ObjectId(request.headers["Conf-Member-Id"])
        _, count = await database.conference_members.get({
            "conference_id": conference_id, 
            "user_id": user_id, 
            "status": {"$not": "blocked"}
        }, {"_id": 1})
        if count < 1:
            raise MissingUserError("you haven't permission to get channels")
        limit = to_inst(self.request.get("limit"), int) or 10
        ind = to_inst(self.request.get("ind"), int) or 0 
        end = ind + limit
        channels, count = await database.channels.get(
            {"conference_id": conference_id})
        channels = channels[ind:end]
        for channel in channels:
            channel.update({"_id": str(channel["_id"])})
        response_data = {
            "begin_ind": ind,
            "end_ind": end,
            "limit": limit,
            "count": count,
            "channels": channels
        }
        return response_data, {}, "getting channels was successful"


    async def post(self):
        request = self.request
        database: Database = request["database"]
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        # member_id = bson.ObjectId(request.headers["Conf-Member-Id"])
        _, count = await database.conference_members.get({
            "conference_id": conference_id, 
            "user_id": user_id, 
            "status": {"$in": ["admin", "owner"]}
        }, {"_id": 1})
        if count < 1:
            raise MissingUserError("you haven't permission to create channel")
        data = await parse_content(request)
        name = data["name"]
        info = data["info"]
        res = await database.channels.add_one({
            "name": name, "info": info})
        if not res or res.inserted_id:
            DBResultError("cannot add new channel")
        return {
            "channel_id": str(res.inserted_id)
        }, {}, "channel was successfully added"


class ChannelView(web.View, mixin.CorsViewMixin):
    async def get(self):
        request = self.request
        database: Database = request["database"]
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        channel_id = bson.ObjectId(request.match_info["channel_id"])
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        # member_id = bson.ObjectId(request.headers["Conf-Member-Id"])
        _, count = await database.conference_members.get({
            "conference_id": conference_id, 
            "user_id": user_id, 
            "status": {"$not": "blocked"}
        }, {"_id": 1})
        if count < 1:
            raise MissingUserError("you haven't permission to create channel")
        channels, count = await database.channels.get({
            "_id": channel_id, "conference_id": conference_id
        }, {"_id": 0})
        if count < 1:
            DBResultError("cannot find channel")
        channel = channels[0]
        return channel, {}, "channel was found"


    async def put(self):
        request = self.request
        database: Database = request["database"]
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        channel_id = bson.ObjectId(request.match_info["channel_id"])
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        _, count = await database.conference_members.get({
            "conference_id": conference_id,
            "user_id": user_id,
            "status": {"$in": ["admin", "owner"]}
        }, {"_id": 1})
        if count < 1:
            raise MissingUserError("you haven't permission to create channel")
        keys = ["name", "info"]
        data = await parse_content(request)
        upd_data = {}
        for k in keys:
            v = data.get(k)
            if v:
                upd_data.update({k: v})
        if not upd_data:
            raise ValueError("not data to update")
        res = await database.channels.update(
            {"channel_id": channel_id}, upd_data)
        if res.modified_count < 1:
            raise DBResultError("cannot update this conference")
        return {}, {}, "channel was updated"


    async def delete(self):
        request = self.request
        database: Database = request["database"]
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        channel_id = bson.ObjectId(request.match_info["channel_id"])
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        _, count = await database.conference_members.get({
            "conference_id": conference_id,
            "user_id": user_id,
            "status": {"$in": ["admin", "owner"]}
        }, {"_id": 1})
        if count < 1:
            raise MissingUserError("you haven't permission to create channel")
        _, count = await database.channels.get(
            {"_id": channel_id, "conference_id": conference_id})
        if count < 1:
            raise ValueError("conference hasn't this channel")
        chats, _ = await database.channel_chats.get(
            {"channel_id", {"_id": 1}})
        chats = [list(chat.values())[0] for chat in chats]
        res = await database.channel_chat_msgs.delete(
            {"chat_id": {"$in": chats}})
        res = await database.channel_members.delete(
            {"channel_id": channel_id})
        res = await database.channels.delete({"_id": channel_id})
        return {}, {}, "channel was deleted"