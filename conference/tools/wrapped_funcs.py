from aiohttp.web import Request


def to_inst(value, cast):
    try:
        return cast(value)
    except:
        return None
    

async def parse_content(request: Request):
    if request.content_type == "application/json":
        data: dict = await request.json()
    else:
        data = await request.post()
    return data