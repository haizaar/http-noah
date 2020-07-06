# Using aiohttp server part since it already comes as part of aiohttp

import asyncio
import socket
from dataclasses import dataclass, field
from http import HTTPStatus

import structlog
from aiohttp import web

from .models import Pet, Pets

routes = web.RouteTableDef()
logger = structlog.get_logger(__name__)


@routes.get("/api/v1/str")
async def get_str(request: web.Request):
    return web.Response(text="boo")


@routes.get("/api/v1/bytes")
async def get_bytes(request: web.Request):
    return web.Response(body=b"bin-boo")


@routes.get("/api/v1/int")
async def get_int(request: web.Request):
    return web.Response(text="1")


@routes.get("/api/v1/json_int")
async def get_json_int(request: web.Request):
    return web.json_response(1)


@routes.get("/api/v1/json_str")
async def get_json_str(request: web.Request):
    return web.json_response("boo")


@routes.delete("/api/v1/pets/1")
async def delete_pet(request: web.Request):
    return web.Response(status=HTTPStatus.NO_CONTENT)


@routes.get("/api/v1/pets/1")
async def get_pet(request: web.Request):
    return web.json_response(Pet(name="foo").dict())


@routes.put("/api/v1/pets/1")
async def put_pet(request: web.Request):
    pet_info = await request.json()
    return web.json_response(Pet(name=pet_info["name"]).dict())


@routes.get("/api/v1/pets")
async def get_pets(request: web.Request):
    pets = Pets(__root__=[Pet(name="foo"), Pet(name="bar")])
    return web.json_response(pets.dict()["__root__"])


@routes.post("/api/v1/pets")
async def post_pets(request: web.Request):
    pet_info = await request.json()
    return web.json_response(Pet(name=pet_info["name"]).dict())


@routes.post("/api/v1/pets/_from_form")
async def post_pets_form(request: web.Request):
    pet_form = await request.post()
    return web.json_response(Pet(name=pet_form["name"]).dict())


@routes.get("/api/v1/pets/2")
async def get_missing_pet(request: web.Request):
    raise web.HTTPNotFound(body="No such pet")


@routes.get("/api/v1/pets/slow")
async def get_slow_pet(request: web.Request):
    # At least 1 second since client measures timeouts in multiples of 1 second
    # https://github.com/aio-libs/aiohttp/issues/4850
    await asyncio.sleep(1.1)
    return web.json_response(Pet(name="slow").dict())


@routes.post("/api/v1/pets/slow")
async def post_slow_pet(request: web.Request):
    # At least 1 second since client measures timeouts in multiples of 1 second
    # https://github.com/aio-libs/aiohttp/issues/4850
    await asyncio.sleep(1.1)
    return web.json_response(Pet(name="slow").dict())


@routes.put("/api/v1/pets/slow")
async def put_slow_pet(request: web.Request):
    # At least 1 second since client measures timeouts in multiples of 1 second
    # https://github.com/aio-libs/aiohttp/issues/4850
    await asyncio.sleep(1.1)
    return web.json_response(Pet(name="slow").dict())


@routes.delete("/api/v1/pets/slow")
async def delete_slow_pet(request: web.Request):
    # At least 1 second since client measures timeouts in multiples of 1 second
    # https://github.com/aio-libs/aiohttp/issues/4850
    await asyncio.sleep(1.1)
    return web.json_response(Pet(name="slow").dict())


@dataclass
class Server:
    port: int = field(init=False)
    sock: socket.socket = field(init=False)
    site: web.SockSite = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
        self.sock.bind(("localhost", 0))
        _, self.port = self.sock.getsockname()

    async def start(self) -> None:
        app = web.Application()
        app.add_routes(routes)
        runner = web.AppRunner(app)
        await runner.setup()
        self.site = web.SockSite(runner=runner, sock=self.sock)
        await self.site.start()
        logger.info("Server is up", port=self.port)

    async def stop(self) -> None:
        await self.site.stop()
        logger.info("Server stopped")
        self.sock.close()