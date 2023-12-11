from aiohttp import web
from aiohttp_cors import mixin
import bson
import logging

from tools.database import Database
from tools.exceptions import UniqueDataError, MissingUserError, DBResultError
from tools.wrapped_funcs import to_inst, parse_content


class ConferencesView(web.View, mixin.CorsViewMixin):
    async def get(self):
        request = self.request
        database: Database = request["database"]
        limit = to_inst(self.request.get("limit"), int) or 10
        ind = to_inst(self.request.get("ind"), int) or 0 
        end = ind + limit
        conferences, count = database.conferences.get({})
        conferences = conferences[ind:end]
        for conference in conferences:
            conference.update({"_id": str(conference["_id"])})
        response_data = {
            "begin_ind": ind,
            "end_ind": end,
            "limit": limit,
            "count": count,
            "conferences": conferences
        }
        return response_data, {}, "getting conferences was successful"


    async def post(self):
        request = self.request
        database: Database = request["database"]
        data = await parse_content(request)
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        res = await database.conferences.add_one({
            "name": data["name"],
            "info": data["info"],
            "password": data["password"]
        })
        if not res or res.inserted_id:
            raise DBResultError("cannot add conference")
        conference_id = res.inserted_id
        res = await database.conference_members.add_one({
            "user_id": user_id,
            "conference_id": conference_id,
            "status": "owner"
        })
        if not res or res.inserted_id:
            raise DBResultError("cannot add conference member")
        response_data = {
            "conference_id": conference_id
        }
        return response_data, {}, "conference was created"
    

class ConferenceView(web.View, mixin.CorsViewMixin):
    async def get(self):
            request = self.request
            database: Database = request["database"]
            user_id = bson.ObjectId(request.headers["Conf-User-Id"])
            _, count = await database.conference_members.get({
                "user_id": user_id, 
                "status": {"$not": "blocked"}
            }, {"_id": 1})
            if count < 1:
                raise MissingUserError("you cannot join to this conference")
            conference_id = bson.ObjectId(request.match_info["conference_id"])
            conference, count = await database.conferences.get({
                "_id": conference_id
            }, {"_id": 0})
            if count < 1:
                raise DBResultError("there is not such conference")
            conference = conference[0]
            return conference, {}, "conference was found"


    async def put(self):
        request = self.request
        database: Database = request["database"]
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        _, count = await database.conference_members.get({
            "user_id": user_id, 
            "conference_id": conference_id,
            "status": {"$in": ["owner", "admin"]}
        }, {"_id": 1})
        if count < 1:
            raise MissingUserError("you cannot update this conference")
        data = await parse_content(request)
        action = request.get("action")
        if action == "reset_password":
            old_password = data["old_pssword"]
            new_password = data["new_pssword"]
            res = await database.conferences.update({
                "_id": conference_id, "password": old_password
            }, {"password": new_password})
        else:
            keys = ["name", "info"]
            upd_data = {}
            for k in keys:
                v = data.get(k)
                if v:
                    upd_data.update({k: v})
            res = await database.conferences.update({
                "_id": conference_id
            }, upd_data)
        if res.modified_count < 1:
            raise DBResultError("cannot update this conference")
        return {}, {}, "conference was updated"


    async def delete(self):
        request = self.request
        database: Database = request["database"]
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        _, count = await database.conference_members.get({
            "user_id": user_id, 
            "conference_id": conference_id,
            "status": "owner"
        }, {"_id": 1})
        if count < 1:
            raise MissingUserError("you cannot delete this conference")
        channels, _ = await database.channels.get(
            {"conference_id": conference_id}, {"_id": 1})
        channels = [list(v.values())[0] for v in channels]
        channel_chats, _ = await database.channel_chats.get(
            {"channel_id": {"$in": channels}}, {"_id": 1})
        channel_chats = [list(v.values())[0] for v in channel_chats]
        messages, _ = await database.channel_chat_msgs(
            {"chat_id": {"$in": channel_chats}}, {"_id": 1})
        messages = [list(v.values())[0] for v in messages]
        res = await database.channel_chat_msg_files.delete(
            {"message_id": {"$in": messages}})
        res = await database.conference_members.delete(
            {"conference_id": conference_id})
        res = await database.channels.delete(
            {"conference_id": conference_id})
        res = await database.channel_chats.delete(
            {"channel_id": {"$in": channels}})
        res = await database.channel_chat_msgs.delete(
            {"chat_id": {"$in": channel_chats}})
        res = await database.conferences.delete({"_id": conference_id})
        return {}, {}, "conference was deleted"