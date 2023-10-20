from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto

from fastapi import WebSocket


class State(Enum):
    WAITING_FOR_JOIN = auto()
    WAITING_FOR_PLAYERS_CHOOSE = auto()
    ROUND_LOCKED = auto()
    CLOSED = auto()


@dataclass
class Player:
    token: str
    ws_connection: WebSocket
    nickname: str


@dataclass
class Room:
    room_id: int
    round_number: int = 1
    rounds: dict = field(default_factory=lambda: defaultdict(dict))
    states: list[State] = field(default_factory=lambda: [State.WAITING_FOR_JOIN])
    players: dict[str, Player] = field(default_factory=dict)

    @property
    def latest_state(self):
        return self.states[-1]

    def get_current_round(self):
        return self.rounds[self.round_number]
