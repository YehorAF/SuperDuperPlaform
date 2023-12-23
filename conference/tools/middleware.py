from aiohttp import web
from bson import ObjectId, errors
from typing import Callable, Awaitable
import logging

from tools.database import Database
from tools.exceptions import UniqueDataError, MissingUserError, DBResultError

_database: Database = None


@web.middleware
async def auth_middleware(
    request: web.Request, 
    handler: Callable[[web.Request], Awaitable[web.Response]]
):
    try:
        database: Database = request.app["database"]
        user = request.headers.get("Conf-User-Id")
        session = request.headers.get("Conf-User-Session")
        api_key = request.headers.get("Conf-Api-Key")
        # it is bad choice to write code
        # i should to replace it on better (use functions for this task)
        if not api_key or api_key not in request.app["app_keys"]:
            if not user or not session:
                return web.json_response({
                    "status": "fail", 
                    "description": "user doesn't authorized"
                }, status=403)
            _, count = await database.users.get({
                "_id": ObjectId(user), 
                "session": session, 
                "status": {"$not": "blocked"}
            }, {"_id": 1})
            if count < 1:
                return web.json_response({
                    "status": "fail", 
                    "description": "user doesn't authorized"
                }, status=403)
        return await handler(request)
    except errors.InvalidId as ex_:
        logging.warning(ex_)
        return web.json_response({
            "status": "fail",
            "description": "bad user_id"
        }, status=400)


@web.middleware
async def exceptions_handler_middleware(
    request: web.Request, 
    handler: Callable[[web.Request], Awaitable[web.Response]]
):
    status_code = 500
    status = "fail"
    description = "server error"
    response_data = {}
    headers = {}
    try:
        response_data, headers, message = await handler(request)
        status_code = 200
        status = "ok"
    except MissingUserError as ex_:
        logging.debug(ex_)
        status_code = 403
        description = str(ex_)
    except KeyError as ex_:
        logging.debug(f"not such field: {ex_}")
        status_code = 400
        description = f"not such field: {ex_}"
    except ValueError as ex_:
        logging.debug(ex_)
        status_code = 400
        description = str(ex_)
    except DBResultError as ex_:
        logging.warning(ex_)
        status_code = 400
        description = str(ex_)
    except errors.InvalidId as ex_:
        logging.warning(ex_)
        status_code = 400
        description = "invalid field or header"
    except Exception as ex_:
        logging.error(ex_)
    return web.json_response({
        "status": status,
        "description": description
    } | response_data, status=status_code, headers=headers)