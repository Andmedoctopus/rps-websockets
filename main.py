import random
import string
from fastapi import (
    Cookie,
    FastAPI,
    WebSocket,
    Query,
    WebSocketException,
    status,
    Depends,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse
from typing import Annotated

from game_master import GameMaster
from game import Game
from entity import Player,  Room
from fastapi.middleware.cors import CORSMiddleware
import pydantic


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
    return FileResponse("index.html")


game_master = GameMaster(game=Game())

users = {}

async def get_user_token(
    session: Annotated[str | None, Cookie()] = None,
    token: Annotated[str | None, Query()] = None,
) -> str:
    if token is not None:
        return token
    if session is not None:
        return session
    raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)


class User(pydantic.BaseModel):
    nickname: str

@app.post("/user")
async def create_user_token(user: User) -> dict:
    print('going to add user')
    user_id = ''.join(random.choices(string.ascii_letters, k=8))
    users[user_id] = user.nickname
    print('added user')
    return {"token": user_id}

@app.websocket("/room/{room_id}")
async def room(
    websocket: WebSocket,
    room_id: int,
    user_token: Annotated[str, Depends(get_user_token)],
):
    print(users)
    if user_token not in users:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="You have to get token first")
    player=Player(
        token=user_token,
        ws_connection=websocket,
        nickname=users[user_token],
    )
    try:
        await game_master.join_room(room_id, player)
    except ValueError as exc:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=exc.args[0])

    while True:
        print("start process", websocket, user_token)
        try:
            command = await websocket.receive_json()
            await game_master.process_command(command, player)
        except WebSocketDisconnect:
            await game_master.disconnect(player)
            break
        print("finish process", websocket, user_token)
