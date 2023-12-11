from aiohttp import web
from aiohttp_cors import mixin
import aiohttp_jinja2
import bson
import socketio
import logging

from tools.database import Database


class ConferenceView(web.View, mixin.CorsViewMixin):
    @aiohttp_jinja2.template("index.html")
    async def get(self, *args, **kwargs):
        pass


    async def post(self, *args, **kwargs):
        database: Database = self.request.app["database"]
        status_code = 500
        status = "fail"
        description = "server error"
        response_data = {}

        try:
            content_type = self.request.content_type
            if content_type == "application/json":
                data: dict = await self.request.json()
            else:
                data = await self.request.post()

            name = data["name"]
            info = data["info"]
            password = data["password"]
            res = await database.conferences.add_one({
                "name": name,
                "password": password,
                "info": info
            })
            conference_id = res.inserted_id
            user_conf_id = self.request.headers["User-Conf-Id"]

            await database.conference_members.add_one({
                "user_id": bson.ObjectId(user_conf_id),
                "conference_id": conference_id,
                "status": "owner"
            })

            status_code = 200
            status = "ok"
            description = "conference was created"
            response_data = {
                "conference_id": str(conference_id)
            }
        except KeyError as ex_:
            logging.debug(f"not such field {ex_}")
            status_code = 400
            description = f"not such field {ex_}"
        except Exception as ex_:
            logging.error(f"error on server: {ex_}")

        return web.json_response({
            "status": status,
            "description": description,
        } | response_data, status=status_code)
    

    # async def put(self, *args, **kwargs):
    #     status_code = 500
    #     status = "fail"
    #     description = "server error"
    #     response_data = {}

    #     try:
    #         content_type = self.request.content_type
    #         if content_type == "application/json":
    #             data: dict = await self.request.json()
    #         else:
    #             data = await self.request.post()
    #             data = dict(data)
    #         st_data = {}
    #         for k in ["name", "info"]:
    #             v = data.get(k)
    #             if v:
    #                 st_data |= {k: v}
    #         await _database.conferences.update()
    #     except:
    #         pass


    # async def delete(self, *args, **kwargs):
    #     pass


# потрібно буде додати менеджер, щоб видаляв пусті конекти
class StreamHandler(socketio.AsyncNamespace):
    async def on_connect(self, sid, *args, **kwargs):
        pass


    async def on_join(self, sid, data):
        room = data["room"]
        await self.enter_room(sid, room)
        await self.emit(
            event="ready", 
            data={"sid": sid}, #"username": username}, 
            room=room, 
            skip_sid=sid
        )


    async def on_quit(self, sid, data):
        room = data["room"]
        await self.leave_room(sid, room)


    async def on_disconnect(self, sid):
        pass


    async def on_connect_error(self, sid, data):
        print(sid, data)


    async def on_data(self, sid, data: dict):
        # username = request["username"]
        room = data.get("room")
        send_to = data.get("sid")
        data = data | {"sid": sid}
        await self.emit(
            event="data", data=data, room=(send_to or room), skip_sid=sid)

# api/v1/conference - get, post
# api/v1/conference/{conf_id} - get, post, put, delete
# api/v1/user - get, post
# api/v1/user/{user_id} - get, post, put, delete
# api/v1/conference/{conf_id}/channel - get, post
# api/v1/conference/{conf_id}/channel/{channel_id} - get, put, delete
# api/v1/conference/{conf_id}/member - get, post
# api/v1/conference/{conf_id}/member/{member_id} - get, put, delete
# api/v1/conference/{conf_id}/channel/{channel_id}/chat - get, post
# api/v1/conference/{conf_id}/channel/{channel_id}/chat/{chat_id} - get, put, delete