import asyncio
from motor.core import AgnosticCursor
import motor.core as core
import motor.motor_asyncio as mtr
import typing


class Collection:
    def __init__(self, collection) -> None:
        self._collection: core.AgnosticCollection = collection


    async def add_one(self, data: dict) -> core.AsyncCommand:
        return await self._collection.insert_one(data)
    

    async def add_many(self, data: list[dict]) -> core.AsyncWrite:
        return await self._collection.insert_many(data)
    

    async def update(self, query: dict, data: dict) -> core.AsyncCommand:
        return await self._collection.update_many(query, {"$set": data})
    

    async def delete(self, query: dict) -> core.AsyncCommand:
        return await self._collection.delete_many(query)
    

    async def get(self, query: dict, *args, **kwargs
                  ) -> typing.Tuple[AgnosticCursor, int]:
        return await (self._collection.find(query, *args, **kwargs), 
                      await self._collection.count_documents(query))
    

class Users(Collection):
    pass


class Conferences(Collection):
    pass


class ConferenceMembers(Collection):
    pass


class Channels(Collection):
    pass


class ChannelChats(Collection):
    pass


class ChannelMembers(Collection):
    pass


class ChannelChatMsgs(Collection):
    pass


class Database:
    def __init__(self, url: str, dbname: str) -> None:
        self._client: core.AgnosticClient = mtr.AsyncIOMotorClient(url)
        self._db: core.AgnosticBase = self._client[dbname]
        self.users = Users(self._db.users)
        self.conferences = Conferences(self._db.conferences)
        self.conference_members = ConferenceMembers(self._db.conference_members)
        self.channels = Channels(self._db.channels)
        self.channel_chats = ChannelChats(self._db.channel_chats)
        self.channel_members = ChannelMembers(self._db.channel_members)
        self.channel_chat_msgs = ChannelChatMsgs(self._db.channel_chat_msgs)


# database structure
# users {id, name, info, photo, session}
# conference {id, name, info, password} remove password
# conference_member {id, conference_id, user_id, status}
# channel_members {id, sid, channel_id, member_id, timestamp}
# channel {id, conference_id, name, info}
# channel_chat {id, channel_id, conference_id, name, info}
# channel_chat_message {id, chat_id, member_id, user_id, text, files}