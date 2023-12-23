from aiohttp import ClientSession


create_user = {
    
}



async def create_user(host: str, headers: dict, data: dict):
    async with ClientSession(headers=headers) as session:
        response = await session.post(f"{host}/user", data=data)
        print(await response.text())