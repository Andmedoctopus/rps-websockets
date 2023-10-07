from fastapi import (
    FastAPI,
    WebSocket,
    Query,
    WebSocketException,
    status,
    Depends,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse
from typing import Annotated

from game_master import GameMaster
from game import Game
from entity import Player,  Room

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Rock Paper Scissors</title>
    </head>
    <body>
        <h1>Rock Paper Scissor</h1>
        <form action="" onsubmit="joinRoom(event)">
        <h2>Your token: <span id="ws-jwt"></span></h2>
            <input type="text" id="token" autocomplete="off"/>
            <button id="join">Join</button>
        </form>

        <form action="" onsubmit="sendAction(event)" style="flex-direction: row;display: flex;">
            <button id="rock" style="display: none">🪨</button>
            <button id="paper" style="display: none">📜</button>
            <button id="scissors" style="display: none">✂️</button>
        </form>

        <ul id='messages'>
        </ul>
        <script>
            let ws = null;

            function joinRoom(event) {
                let token = document.getElementById("token").value
                ws = new WebSocket(`ws://localhost:8000/room/666?token=${token}`);
                ws.onmessage = function(event) {
                    let messages = document.getElementById('messages')
                    let message = document.createElement('li')
                    let content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };

                for (const id of ['rock', 'paper', 'scissors']) {
                    let gameElem = document.getElementById(id);
                    gameElem.style.display = "block"
                }

                event.preventDefault()
            }

            function sendAction(event) {
                let choice = {choice: event.submitter.id}
                ws.send(JSON.stringify(choice))
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)




game_master = GameMaster(game=Game())


async def get_user_token(
    token: Annotated[str | None, Query()] = None,
):
    if token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return token



@app.websocket("/room/{room_id}")
async def room(
    websocket: WebSocket,
    room_id: int,
    user_token: Annotated[str, Depends(get_user_token)],
):
    player=Player(
        token=user_token,
        ws_connection=websocket,
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
