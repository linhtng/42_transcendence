import asyncio
import json
from django.core.cache import cache
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.http import Http404
from django.shortcuts import get_object_or_404

from .game_loop import GameLoop
from .game_state import GameState


import logging

from .models import Match, Player, Tournament

logger = logging.getLogger(__name__)

games = {}


class PongConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tournament = None
        self.tournament_id = None
        self.pong_group_name = None
        self.game_loop = None
        self.username = None  # for debug

    # HELPER METHODS

    @database_sync_to_async
    def get_tournament_by_id(self, tournament_id):
        try:
            return get_object_or_404(Tournament, tournament_id=tournament_id)
        except (Tournament.DoesNotExist, Http404):
            logger.error(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Tournament with id {tournament_id} does not exist"
            )
            return None

    @database_sync_to_async
    def get_player_by_user(self, user):
        try:
            player = get_object_or_404(Player, user=user)
            return player
        except Player.DoesNotExist:
            return None
        except Http404:
            return None

    @database_sync_to_async
    def is_tournament_full(self):
        try:
            return self.tournament.players.count() == self.tournament.num_players
        except Exception as e:
            logger.error(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Error checking if tournament is full: {e}"
            )
            return False

    # GAME LOGIC HANDLERS

    def create_game_loop_if_not_exists(self):
        if not games.get(self.tournament.tournament_id):
            games[self.tournament_id] = GameLoop(
                self.tournament.current_match, self.tournament_id
            )
            logger.info(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Game loop for match {self.tournament.current_match.game_id} created, games dictionary: {games}"
            )
        else:
            logger.info(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Game loop for match {self.tournament.current_match.game_id} already exists, games dictionary: {games}"
            )

    def set_game_loop(self):
        if not self.game_loop:
            self.game_loop = games[self.tournament_id]

    @database_sync_to_async
    def create_1st_match(self):
        try:
            logger.info(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Creating 1st match"
            )
            if not self.tournament.current_match:
                logger.info(
                    f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Setting current_match"
                )
                self.tournament.current_match, created = Match.objects.get_or_create(
                    player1=self.tournament.players.all()[0],
                    player2=self.tournament.players.all()[1],
                    tournament=self.tournament,
                )
                self.tournament.save()
                if created:
                    logger.info(
                        f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] 1st match created"
                    )
                else:
                    logger.info(
                        f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] 1st match already exists"
                    )
            self.create_game_loop_if_not_exists()
            self.set_game_loop()
        except Exception as e:
            logger.error(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Error creating 1st match: {e}"
            )

    @database_sync_to_async
    def determine_tournament_winner(self):
        try:
            logger.info("Determining tournament winner")
            winner = self.tournament.current_match.winner
            self.tournament.winner = winner
            # self.tournament.current_match = None
            # self.tournament.state = "FINISHED"
            # self.tournament.is_final = True
            self.tournament.save()
        except Exception as e:
            logger.error(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Error determining tournament winner: {e}"
            )

    @database_sync_to_async
    def destroy_game(self):
        try:
            logger.info(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Destroying game (commented out)"
            )
            # loop = games[self.tournament_id]
            # loop.running = False
            # loop.stop()
            # logger.info(
            #     f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Game loop stopped"
            # )
            # del games[self.tournament_id]
            # logger.info(
            #     f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Game loop deleted"
            # )
            # self.game_loop = None
            # self.tournament.current_match = None
            # self.tournament.save()
        except Exception as e:
            logger.error(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Error destroying game: {e}"
            )

    # TODO handle tournamernt state. needs to be set to FINISHED at some point

    @database_sync_to_async
    def form_tournament_finished_message(self):
        winner_info = (
            self.tournament.winner.alias if self.tournament.winner else "unknown"
        )
        return {"event": "tournament_finished", "winner": winner_info}

    @database_sync_to_async
    def is_loop_running(self):
        return self.game_loop.running

    async def start_tournament(self):
        try:
            if await self.get_tournament_property("is_started"):
                logger.info(
                    f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Tournament is already started"
                )
                return
            self.set_tournament(is_started=True)
            logger.info(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Starting tournament"
            )

            num_players_expected = await self.get_tournament_property("num_players")
            logger.info(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Number of players expected: {num_players_expected}"
            )
            if await self.get_tournament_property("num_players") == 2:
                await self.create_1st_match()
                # TODO this condition is wrong, check for it to work. We only want loop to run once
                is_loop_running = await self.is_loop_running()
                logger.info(
                    f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Game loop running bool: {is_loop_running}"
                )
                if is_loop_running:
                    logger.info("Game loop is already running")
                    return
                logger.info(
                    f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Game loop is not running, starting it"
                )
                await self.game_loop.loop(
                    f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}]"
                )
                logger.info(
                    f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Game loop over"
                )
                await self.determine_tournament_winner()
                logger.info(
                    f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Determining tournament winner"
                )
                await self.send_message_to_all(
                    await self.form_tournament_finished_message(), "tournament"
                )
                await self.destroy_game()
                await self.set_tournament(state="FINISHED", is_started=False)
                logger.info(
                    f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Tournament finished"
                )
            else:
                logger.info("Not 2 players in tournament")
        except Exception as e:
            logger.error(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Error starting tournament: {e}"
            )
            pass

    @database_sync_to_async
    def form_new_player_message(self, user):
        return {
            "event": "new_player",
            "player_alias": user.username,
            "num_players_in_tournament": self.tournament.players.count(),
            "num_players": self.tournament.num_players,
        }

    @database_sync_to_async
    def form_countdown_message(self, countdown):
        return {
            "event": "countdown",
            "countdown": countdown,
            "player1_alias": "Player1_alias",
            "player2_alias": "Player2_alias",
        }

    @database_sync_to_async
    def get_player_in_current_match(self, user):
        try:
            if not self.tournament:
                logger.info(
                    f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] get_player_in_current_match no tournament"
                )
                return None
            if not self.tournament.current_match:
                logger.info(
                    f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] get_player_in_current_match no current match"
                )
                return None
            if not games.get(self.tournament.tournament_id):
                logger.info(
                    f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] get_player_in_current_match no game in dictionary, this should never happen"
                )
                return None
            if self.tournament.current_match.player1.user == user:
                return 1
            if self.tournament.current_match.player2.user == user:
                return 2
            logger.info(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] get_player_in_current_match end of function"
            )
            return None
        except Exception as e:
            logger.error(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Error in get_player_in_current_match: {e}"
            )

    # CONNECTION HANDLERS

    @database_sync_to_async
    def set_tournament(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.tournament, key):
                setattr(self.tournament, key, value)
        self.tournament.save()

    @database_sync_to_async
    def get_tournament_property(self, propertyKey):
        if hasattr(self.tournament, propertyKey):
            return getattr(self.tournament, propertyKey)
        return None

    async def connect(self):
        try:

            # Get tournament info from the URL
            self.tournament_id = self.scope["url_route"]["kwargs"]["tournament_id"]
            self.pong_group_name = f"group_{self.tournament_id}"
            if not self.tournament:
                self.tournament = await self.get_tournament_by_id(self.tournament_id)

            # Accept the connection always
            await self.channel_layer.group_add(self.pong_group_name, self.channel_name)
            await self.accept()

            # And then reject if user is not authenticated or tournament does not exist
            if not self.tournament or not self.scope["user"].is_authenticated:
                await self.disconnect()
                return
            self.username = self.scope["user"].username
            # Check what's going on with the games dictionary
            logger.info(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Games dictionary: {games}"
            )

            # Get tournament status and start it if needed
            # await self.add_player_to_tournament(self.scope["user"])
            tournament_state = await self.get_tournament_property("state")
            logger.info(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Current tournament state: {tournament_state}"
            )
            tournament_is_started = await self.get_tournament_property("is_started")
            logger.info(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Current tournament is_started: {tournament_is_started}"
            )
            if tournament_is_started is False and tournament_state == "PLAYING":
                logger.info("Starting tournament")
                await self.start_tournament()
            else:
                logger.info("Tournament is not started")

        except Exception as e:

            logger.info(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Error in connect method: {e}"
            )

    def get_tournament_data(self, tournament):
        return {
            "tournament_id": tournament.tournament_id,
            "title": tournament.title,
            "state": tournament.state,
            "num_players": tournament.num_players,
            "players": [player.username for player in tournament.players.all()],
            "winner": tournament.winner.username if tournament.winner else "",
        }

    async def disconnect(self, close_code):
        if self.pong_group_name:
            await self.channel_layer.group_discard(
                self.pong_group_name, self.channel_name
            )

    # SENDING AND RECEIVING MESSAGES

    async def send_message_to_all(self, message, message_type):
        try:
            logger.info(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Sending message of type {message_type} to all in group {self.pong_group_name}"
            )
            await self.channel_layer.group_send(
                self.pong_group_name,
                {
                    "type": "send_message",
                    "message": message,
                    "message_type": message_type,
                },
            )
        except Exception as e:
            logger.info(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Error sending message to all: {e}"
            )

    # TODO: remove if not needed
    # @database_sync_to_async
    # def get_player_number(self):
    #     # Logic to determine if this is player 1 or player 2
    #     # This could be based on the order of connection, user ID, etc.
    #     # For example:
    #     if self.tournament.players.count() == 1:
    #         return 1
    #     else:
    #         return 2

    # async def send_tournament_state_to_all(self, tournament_data):
    #     await self.channel_layer.group_send(
    #         self.pong_group_name,
    #         {"type": "send_tournament_state", "tournament_message": tournament_data},
    #     )

    async def send_message(self, event):
        try:
            message = event["message"]
            type = event["message_type"]
            text_data = await sync_to_async(json.dumps)(
                {"type": type, "message": message}
            )
            await self.send(text_data=text_data)
        except Exception as e:
            logger.error(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Error sending message: {e}"
            )

    # async def send_tournament_state(self, event):
    #     await self.send(
    #         text_data=json.dumps(
    #             {"type": "tournament", "message": event["tournament_message"]}
    #         )
    #     )

    async def receive(self, text_data):

        try:
            user = self.scope["user"]
            # only receive messages from players in the current match, ignore otherwise
            if not user.is_authenticated:
                return
            player_number = await self.get_player_in_current_match(user)
            logger.info(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Player number of user {user}: {player_number}"
            )
            if not player_number:
                return
            # Parse the message and pass it to key press handler
            text_data_json = json.loads(text_data)
            message = text_data_json["message"]
            await sync_to_async(self.set_game_loop)()
            await self.game_loop.handle_key_press(message, player_number)
        except Exception as e:
            logger.error(
                f"[{self.channel_name[-4:]} {self.tournament_id} {self.username}] Error receiving message: {e}"
            )
