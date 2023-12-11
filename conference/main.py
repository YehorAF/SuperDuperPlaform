from aiohttp import web
import aiohttp_cors
import aiohttp_jinja2
import jinja2
from socketio import AsyncServer
import ssl

from tools.database import Database
from tools.middleware import auth_middleware, exceptions_handler_middleware

# from handlers.stream import StreamHandler, ConferenceView
from handlers.channels import ChannelStreamHandler, ChannelView, ChannelsView
from handlers.chats import ChatNamespace, ChatView, ChatsView
from handlers.conference import ConferenceView, ConferencesView
from handlers.members import MemberView, MembersView
from handlers.users import UserView, UsersView

def main():
    # logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)

    app = web.Application(
       middlewares=[auth_middleware, exceptions_handler_middleware])
    database = Database(
       "mongodb://localhost:27017/study_platform", "study_platform")
    app["database"] = database
    app.add_routes([
        web.view("/conference", ConferencesView),
        web.view("/conference/{conference_id}", ConferenceView),
        web.view("/user", UsersView),
        web.view("/user/{user_id}", UserView),
        web.view("/conference/{conference_id}/member", MembersView),
        web.view("/conference/{conference_id}/member/{member_id}", MemberView),
        web.view("/conference/{conference_id}/channel", ChannelsView),
        web.view(
           "/conference/{conference_id}/channel/{channel_id}", ChannelView),
        web.view(
           "/conference/{conference_id}/channel/{channel_id}/chat", ChatsView),
        web.view(
           "/conference/{conference_id}/channel/{channel_id}/chat/{chat_id}", 
           ChatView
        ),
    ])
    server = AsyncServer(async_mode="aiohttp", cors_allowed_origins="*")
    server.attach(app)
    server.register_namespace(
       ChannelStreamHandler(database, "/conference_socks/conf",))
    server.register_namespace(
       ChatNamespace(database, "/conference_socks/chat"))

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain("settings/cert.pem", "settings/key.pem")

    cors = aiohttp_cors.setup(app)

    for resource in app.router._resources:
      if resource.raw_match("/socket.io/"):
        continue
      cors.add(
        resource, 
        { '*': aiohttp_cors.ResourceOptions(
              allow_credentials=True, 
              expose_headers="*", 
              allow_headers="*") 
        })

    web.run_app(app, host="localhost", port=8443, ssl_context=ssl_context)


if __name__ == "__main__":
    main()