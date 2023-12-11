from aiohttp import web
from aiohttp_cors import mixin
import bson
import logging
import secrets

from tools.database import Database
from tools.exceptions import UniqueDataError, MissingUserError, DBResultError
from tools.wrapped_funcs import to_inst, parse_content


class MembersView(web.View, mixin.CorsViewMixin):
    async def get(self):
        request = self.request
        database: Database = request["database"]
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        limit = to_inst(self.request.get("limit"), int) or 10
        ind = to_inst(self.request.get("ind"), int) or 0 
        end = ind + limit
        members, count = database.conference_members.get(
            {"conference_id": conference_id})
        members = members[ind:end]
        for member in members:
            member.update({"_id": str(member["_id"])})
        response_data = {
            "begin_ind": ind,
            "end_ind": end,
            "limit": limit,
            "count": count,
            "conferences": members
        }
        return response_data, {}, "getting members was successful"


    async def post(self):
        request = self.request
        database: Database = request.app["database"]
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        data = await parse_content(request)
        password = data["password"]
        _, count = await database.conferences.get(
            {"_id": conference_id, "password": password}, {"_id": 1})
        if count < 1:
            raise ValueError("this password is incorrect")
        res = await database.conference_members.add_one({
            "user_id": user_id, 
            "conference_id": conference_id, 
            "status": "user"
        })
        if not res or not res.inserted_id:
            raise DBResultError("cannot add member")
        return {}, {"Conf-Member-Id": str(res.inserted_id)}, "member was added"
    

class MemberView(web.View, mixin.CorsViewMixin):
    async def get(self):
        request = self.request
        database: Database = request.app["database"]
        member_id = bson.ObjectId(request.match_info["member_id"])
        members, count = await database.conference_members.get(
            {"_id": member_id}, {"_id": 0})
        if count < 1:
            raise ValueError("there is not such user")
        member = members[0]
        return member, {}, "user was found"


    async def put(self):
        request = self.request
        database: Database = request.app["database"]
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        _, count = await database.conference_members.get({
            "user_id": user_id, 
            "conference_id": conference_id,
            "status": {"$in": ["admin", "owner"]}
        })
        if count < 1:
            raise ValueError("you cannot update member status")
        member_id = bson.ObjectId(request.match_info["member_id"])
        data = await parse_content(request)
        status = data["status"]
        res = await database.conference_members.update({
            "_id": member_id, 
            "conference_id": conference_id, 
            "status": {"$not": "owner"}
        }, {"status": status})
        if res.modified_count < 1:
            raise DBResultError("cannot update this member")
        return {}, {}, "member was updated"


    async def delete(self):
        request = self.request
        database: Database = request.app["database"]
        user_id = bson.ObjectId(request.headers["Conf-User-Id"])
        conference_id = bson.ObjectId(request.match_info["conference_id"])
        member_id = bson.ObjectId(request.match_info["member_id"])
        res = await database.conference_members.delete({
            "_id": member_id,
            "user_id": user_id,
            "conference_id": conference_id
        })
        if res.deleted_count < 1:
            DBResultError(f"cannot delete member: {member_id}")
        return {}, {"Conf-Member-Id": ""}, "member was deleted"