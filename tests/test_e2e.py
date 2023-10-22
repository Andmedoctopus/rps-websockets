import re

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from rps.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_full_game_session(client: TestClient):
    users_token = []

    for i in range(1, 3):
        response = client.post("/api/user", json={"nickname": f"user{i}"})

        assert response.status_code == 200
        assert "token" in response.json()

        users_token.append(response.json()["token"])

    room_id = 1234
    user1_cookie = {"session": users_token[0]}
    user2_cookie = {"session": users_token[1]}

    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/api/room/{room_id}", cookies=user1_cookie):
            pass

    assert exc.match("room .* not exist")

    response = client.post("/api/room", cookies=user1_cookie)
    assert response.status_code == 200
    assert "room_id" in response.json()

    room_id = response.json()["room_id"]

    rounds = [
        ("paper", "paper", "Draw"),
        ("paper", "scissors", ".*user2 won.*"),  # 0:1
        ("rock", "scissors", ".*user1 won.*"),  # 1:1
        ("scissors", "rock", ".*user2 won.*"),  # 1:2
    ]
    with (
        client.websocket_connect(f"/api/room/{room_id}", cookies=user1_cookie) as ws1,
        client.websocket_connect(f"/api/room/{room_id}", cookies=user2_cookie) as ws2,
    ):
        ws1.receive_json()
        for _ in ("joined", "ready"):
            print("f1", ws1.receive_json())
            print("f2", ws2.receive_json())

        for ch1, ch2, expected in rounds:
            ws1.send_json({"choice": ch1})
            ws2.send_json({"choice": ch2})

            for _ in ("choose", "start", "finish"):
                print("s", ws1.receive_json())
                print("s", ws2.receive_json())

            data1 = ws1.receive_json()
            data2 = ws2.receive_json()
            assert data1["message"] == data2["message"]
            assert re.match(expected, data1["message"])

        data1 = ws1.receive_json()
        data2 = ws2.receive_json()
        assert data1["message"] == data2["message"] == "user2 won the game!"
