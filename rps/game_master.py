import asyncio
from collections import Counter

from rps.entity import Player, Room, State
from rps.game import Game


class GameMaster:
    def __init__(self, game: Game):
        self.rooms: dict[int, Room] = {}
        self.player_to_room: dict[str, Room] = {}
        self.game = game

    async def join_room(self, room_id: int, player: Player):
        if room_id not in self.rooms:
            self.rooms[room_id] = Room(room_id=room_id)
        room = self.rooms[room_id]

        if room.latest_state != State.WAITING_FOR_JOIN:
            raise ValueError("The room is full")

        room.players[player.token] = player

        self.player_to_room[player.token] = room

        await player.ws_connection.accept()
        await self.notify_room(f"User #{player.nickname} joined", room_id)

        if len(room.players) == 2:
            room.states.append(State.WAITING_FOR_PLAYERS_CHOOSE)
            await self.notify_room("We are ready. Make your choice", room_id)

    async def disconnect(self, player: Player):
        room = self.player_to_room[player.token]

        room.players.pop(player.token)
        self.player_to_room.pop(player.token)

        await self.notify_room(f"User #{player.nickname} left the game", room.room_id)

    async def process_command(self, command: dict, player: Player):
        print(f"{command=}")
        room = self.player_to_room[player.token]

        if room.latest_state == State.CLOSED:
            await self.notify_user({"message": "Game is closed!"}, player.token)
            return

        if room.latest_state == State.WAITING_FOR_JOIN:
            await self.notify_user({"error": "Wait for other player"}, player.token)
            return

        if room.latest_state == State.ROUND_LOCKED:
            await self.notify_user(
                {"message": "Round locked. You can't choose"}, player.token
            )
            return

        if room.latest_state != State.WAITING_FOR_PLAYERS_CHOOSE:
            raise ValueError("Unpexpected status")

        if "choice" in command:
            choice = command["choice"]
            room.rounds[room.round_number][player.token] = choice
            await self.notify_user({"message": f"You choose {choice}"}, player.token)

        if len(room.rounds[room.round_number]) == 2:
            delay = 1
            await self.notify_room(
                f"Round {room.round_number} will be closed in next {delay} seconds. "
                "The round locked. No change now",
                room.room_id,
            )
            await self.lock_round_with_delay(room.room_id, delay)

        print(f"{room.rounds=}")

    async def notify_room(self, message: str, room_id: int):
        for player in self.rooms[room_id].players.values():
            await player.ws_connection.send_json({"message": message})

    async def notify_user(self, message: dict, user_token: str):
        player = self.player_to_room[user_token].players[user_token]
        await player.ws_connection.send_json(message)

    async def determ_round_winner(self, room_id: int):
        room = self.rooms[room_id]

        current_round = room.get_current_round()

        player1, player2 = current_round.items()

        if player1[1] == player2[1]:
            await self.notify_room("Draw", room_id)
            self.start_next_round(room_id)
            return

        if self.game.beat(player1[1], player2[1]):
            winner = player1
        else:
            winner = player2

        current_round["winner"] = winner[0]

        choice = winner[1]
        player = room.players[winner[0]]
        await self.notify_room(f"Player #{player.nickname} won with {choice}", room_id)

        if self.can_game_be_over(room_id):
            await self.finish_game(room_id)
            return

        self.start_next_round(room_id)

    def can_game_be_over(self, room_id) -> bool:
        room = self.rooms[room_id]
        need_to_win = 2

        if len(room.rounds) >= need_to_win:
            counter = Counter(
                game_round["winner"]
                for game_round in room.rounds.values()
                if "winner" in game_round
            ).items()
            if len(counter) != 2:
                return False

            player1, player2 = counter
            p1_won_amount = player1[1]
            p2_won_amount = player2[1]
            if p1_won_amount > p2_won_amount and p1_won_amount >= need_to_win:
                return True

            if p1_won_amount < p2_won_amount and p2_won_amount >= need_to_win:
                return True

        return False

    async def finish_game(self, room_id):
        room = self.rooms[room_id]
        latest_round = room.get_current_round()
        player = room.players[latest_round["winner"]]
        await self.notify_room(f"{player.nickname} won the game!", room_id)
        room.states.append(State.CLOSED)

    def start_next_round(self, room_id):
        room = self.rooms[room_id]
        room.states.append(State.WAITING_FOR_PLAYERS_CHOOSE)
        room.round_number += 1

    async def lock_round_with_delay(self, room_id: int, delay=3):
        room = self.rooms[room_id]

        room.states.append(State.ROUND_LOCKED)
        for sec in range(delay, 0, -1):
            await self.notify_room(
                f"Round {room.round_number} will be finished in {sec}...", room_id
            )
            await asyncio.sleep(1)

        await self.determ_round_winner(room_id)
