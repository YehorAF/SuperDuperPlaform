from aiohttp import web
from aiohttp_cors import mixin
import bson
import logging
import secrets

from tools.database import Database
from tools.exceptions import UniqueDataError, MissingUserError, DBResultError
from tools.wrapped_funcs import to_inst, parse_content


class UsersView(web.View, mixin.CorsViewMixin):
    async def get(self):
        request = self.request
        database: Database = request.app["database"]
        limit = to_inst(self.request.get("limit"), int) or 10
        ind = to_inst(self.request.get("ind"), int) or 0 
        end = ind + limit
        users, count = database.users.get({})
        users = users[ind:end]
        for user in users:
            user.update({"_id": str(user["_id"])})
        response_data = {
            "begin_ind": ind,
            "end_ind": end,
            "limit": limit,
            "count": count,
            "users": users
        }
        return response_data, {}, "getting users was successful"

    async def post(self):
        request = self.request
        database: Database = request.app["database"]
        data = await parse_content(request)
        username = data["username"]
        _, count = await database.users.get(
            {"username": username}, {"_id": 1}) 
        if count > 0:
            raise UniqueDataError("such user exists")
        name = data["name"]
        info = data["info"]
        photo = data["photo"]
        session = secrets.token_urlsafe(16)
        res = await database.users.add_one({
            "name": name,
            "info": info,
            "photo": photo,
            "session": session
        })
        if not res or not res.inserted_id:
            raise DBResultError("cannot add user")
        headers = {
            "Conf-User-Id": str(res.inserted_id),
            "Conf-User-Session": session
        }
        return {}, headers, "user was created"


class UserView(web.View, mixin.CorsViewMixin):
    async def get(self):
        request = self.request
        database: Database = request.app["database"]
        user = request.match_info["user"]
        user_id = to_inst(user, bson.ObjectId)
        if user_id:
            query = {"_id": user_id}
        else:
            query = {"username": user}
        user, count = await database.users.get(query, {"_id": 0})
        if count < 1:
            raise MissingUserError(f"not such user {user}")
        return user, {}, "user was found"
    

    async def put(self):
        request = self.request
        database: Database = request.app["database"]
        user_id = to_inst(request.headers["Conf-User-Id"], bson.ObjectId)
        upd_user_id = to_inst(request.match_info["user"], bson.ObjectId)
        if user_id != upd_user_id:
            raise MissingUserError(
                "you haven't permission to update that user")
        data = await parse_content(request)
        keys = ["name", "info", "photo"]
        upd_data = {}
        for k in keys:
            v = data.get(k)
            if v:
                upd_data.update({k: v})
        if not upd_data:
            raise ValueError("there are not such fields to update")
        session = secrets.token_urlsafe(16)
        res = await database.users.update({
            "_id": user_id
        }, upd_data | {"session": session})
        if res.modified_count < 1:
            raise DBResultError("cannot update user")
        headers = {
            "Conf-User-Id": str(res.inserted_id),
            "Conf-User-Session": session   
        }
        return {}, headers, "user was updated"
    
    # bag with deleting conf
    async def delete(self):
        request = self.request
        database: Database = request.app["database"]
        user_id = to_inst(request.headers["Conf-User-Id"], bson.ObjectId)
        del_user_id = to_inst(request.match_info["user"], bson.ObjectId)
        if user_id != del_user_id:
            raise MissingUserError(
                "you haven't permission to update that user")
        res = await database.users.delete({"_id": user_id})
        if res.deleted_count < 1:
            DBResultError(f"cannot delete user: {user_id}")
        headers = {
            "Conf-User-Id": "",
            "Conf-User-Session": ""
        }
        return {}, headers, "user was deleted"