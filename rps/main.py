import random
import string
from typing import Annotated

import pydantic
from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    Query,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from rps.entity import Player
from rps.game import Game
from rps.game_master import GameMaster

app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def get():
    return FileResponse("rps/index.html")


game_master = GameMaster(game=Game())

users = {}
rooms = set()


async def get_user_token(
    session: Annotated[str | None, Cookie()] = None,
    token: Annotated[str | None, Query()] = None,
) -> str:
    if token is not None:
        return token
    if session is not None:
        return session
    raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)


class UserPayload(pydantic.BaseModel):
    nickname: str


class CreatedUser(pydantic.BaseModel):
    token: str


@app.post("/api/user")
async def create_user_token(user: UserPayload) -> CreatedUser:
    user_id = "".join(random.choices(string.ascii_letters, k=8))
    users[user_id] = user.nickname
    return CreatedUser(token=user_id)


class CreatedRoom(pydantic.BaseModel):
    room_id: int


@app.post("/api/room")
async def create_room(
    user_token: Annotated[str, Depends(get_user_token)],
) -> CreatedRoom:
    while True:
        room_id = random.randint(10000, 99999)
        if room_id not in rooms:
            rooms.add(room_id)
            return CreatedRoom(room_id=room_id)


@app.websocket("/api/room/{room_id}")
async def join_room(
    websocket: WebSocket,
    room_id: int,
    user_token: Annotated[str, Depends(get_user_token)],
):
    if room_id not in rooms:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="This room does not exist"
        )
    if user_token not in users:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="You have to get token first"
        )

    player = Player(
        token=user_token,
        ws_connection=websocket,
        nickname=users[user_token],
    )
    try:
        await game_master.join_room(room_id, player)
    except ValueError as exc:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason=exc.args[0]
        )

    while True:
        print("start process", websocket, user_token)
        try:
            command = await websocket.receive_json()
            await game_master.process_command(command, player)
        except WebSocketDisconnect:
            await game_master.disconnect(player)
            break
        print("finish process", websocket, user_token)
