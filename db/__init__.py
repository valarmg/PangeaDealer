import os
import logging
from pymongo import MongoClient
from bson import ObjectId
from utils.errors import PangeaException, PangaeaDealerErrorCodes
from datetime import datetime
from models import *


def as_objectid(value):
    return None if value is None else ObjectId(str(value))


def get_id(obj):
    value = None
    if obj is None:
        value = None
    elif hasattr(obj, "id"):
        value = obj.id
    elif "id" in obj:
        value = obj["id"]
    elif "_id" in obj:
        value = obj["_id"]
    return as_objectid(value)


class PangeaDb(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        if "OPENSHIFT_MONGODB_DB_URL" in os.environ:
            self.client = MongoClient(os.environ["OPENSHIFT_MONGODB_DB_URL"])
        else:
            self.client = MongoClient("localhost", 27017)

        self.db = self.client.pangea
        self.logger.debug("Opened connection to database")

    # -- Lobby -- #
    def lobby_create(self, name):
        lobby = {
            "name": name,
            "updated_on": datetime.utcnow()
        }
        self.db.lobby.insert(lobby)

        return Lobby().from_dict(lobby)

    def lobby_update(self, lobby_id, name):
        lobby_id = as_objectid(lobby_id)
        lobby = {
            "_id": lobby_id,
            "name": name,
            "updated_on": datetime.utcnow()
        }

        self.db.lobby.update({"_id": lobby_id}, lobby)

    def lobby_delete(self, lobby_id):
        lobby_id = as_objectid(lobby_id)
        self.db.lobby.remove({"_id": lobby_id})

    def lobby_delete_all(self):
        self.db.lobby.remove({})

    def lobby_get_by_id(self, lobby_id):
        lobby = self.db.lobby.find_one({"_id": as_objectid(lobby_id)})
        if lobby is None:
            raise PangeaException(PangaeaDealerErrorCodes.NotFoundError, "Lobby not found")
        return Lobby.from_db(lobby)

    def lobby_get_all(self):
        results = list(self.db.lobby.find())

        lobbies = []
        for document in results:
            lobbies.append(Lobby().from_db(document))
        return lobbies

    # -- Table -- #
    def table_create(self, lobby_id, name):
        lobby_id = as_objectid(lobby_id)

        table = {
            "lobby_id": lobby_id,
            "name": name,
            "updated_on": datetime.utcnow()
        }

        table_id = self.db.table.insert(table)
        self.db.lobby.update({"_id": lobby_id}, {"$push": {"tables": table_id}})
        return Table().from_dict(table)

    def table_update(self, table_id, name):
        table_id = as_objectid(table_id)

        table = {
            "_id": table_id,
            "name": name,
            "updated_on": datetime.utcnow()
        }

        self.db.table.update(table)

    def table_remove(self, table_id):
        table_id = as_objectid(table_id)
        table = self.db.table.find_one({"_id": table_id})

        if table is not None:
            self.db.lobby.update({"_id": table.lobby_id}, {"pull": {"tables": table_id}})
            self.db.lobby.update({"_id": table.lobby_id}, {"set": {"updated_on": datetime.utcnow()}})
            self.db.table.remove({"_id": table_id})
            self.db.event.remove({"table_id", table_id})

    def table_get_by_id(self, table_id):
        table = self.db.table.find_one({"_id": as_objectid(table_id)})

        if table is None:
            raise PangeaException(PangaeaDealerErrorCodes.NotFoundError, "Table not found")
        return Table().from_db(table)

    def table_set_dealer_seat(self, table_id, seat_number):
        table_id = as_objectid(table_id)
        self.db.table.update({"_id": table_id},
                             {"set": {"updated_on": datetime.utcnow(), "dealer_seat_number": seat_number}})

    def table_set_player_seat(self, table_id, seat_number):
        table_id = as_objectid(table_id)
        self.db.table.update({"_id": table_id},
                             {"set": {"updated_on": datetime.utcnow(), "player_seat_number": seat_number}})

    def table_set_dealing_to_seat(self, table_id, seat_number):
        table_id = as_objectid(table_id)
        self.db.table.update({"_id": table_id},
                             {"set": {"updated_on": datetime.utcnow(), "dealing_to_seat_number": seat_number}})

    def table_set_turn_time_start(self, table_id, start_time):
        table_id = as_objectid(table_id)
        self.db.table.update({"_id": table_id},
                             {"set": {"updated_on": datetime.utcnow(), "turn_time_start": start_time}})
        return start_time

    def table_deal_hole_cards(self, table_id, seat_number, cards):
        table_id = as_objectid(table_id)
        self.db.table.update({"_id": table_id, "seats.seat_number": seat_number},
                             {"set": {"seats.hole_cards": cards}})
        self.table_set_updated(table_id)

    def table_deal_board_cards(self, table_id, cards):
        table_id = as_objectid(table_id)
        self.db.table.update({"_id"}, table_id, {"set": {"board_cards": cards}})
        self.table_set_updated(table_id)

    def table_set_current_round(self, table_id, current_round):
        table_id = as_objectid(table_id)
        self.db.table.update({"_id"}, table_id, {"set": {"current_round": current_round}})
        self.table_set_updated(table_id)

    def table_get_by_lobby_id(self, lobby_id):
        results = list(self.db.table.find({"lobby_id": as_objectid(lobby_id)}))

        tables = []
        for document in results:
            tables.append(Table().from_db(document))
        return tables

    def table_get_all(self):
        results = list(self.db.table.find({}))

        tables = []
        for document in results:
            tables.append(Table().from_db(document))
        return tables

    def table_set_updated(self, table_id):
        table_id = as_objectid(table_id)
        self.db.table.update({"_id": table_id}, {"$set": {"updated_on": datetime.utcnow()}})

    def table_set_deck(self, table_id, deck):
        table_id = as_objectid(table_id)
        self.db.table.update({"_id": table_id}, {"$set": {"deck_cards": deck}})

    def table_end_hand(self, table_id):
        table_id = as_objectid(table_id)
        self.db.table.update({"_id": table_id}, {"$set": {
            "player_seat_number": None,
            "current_round": Round.NA,
            "turn_time_start": None,
            "board_card": [],
            "deck_cards": [],
            "current_bet": None,
            "dealing_to_seat_number": None,
            "pot": 0,
            "updated_on": datetime.utcnow(),
        }})

    def table_reset_seats(self, table_id, seat_numbers):
        table_id = as_objectid(table_id)
        for seat_number in seat_numbers:
            self.db.table.update({"_id": table_id, "seats.seat_number": seat_number},
                                 {"$set": {"seats.$.playing": True, "seats.$.hole_cards": None, "seats.$.bet": None}},
                                 upsert=True)

    # --  Player -- #
    def player_create(self, username):
        username_lower = username if username else None

        player = {
            "username": username,
            "username_lower": username_lower,
            "updated_on": datetime.utcnow()
        }

        self.db.player.insert(player)
        return Player().from_dict(player)

    def player_update(self, player_id, username):
        player_id = as_objectid(player_id)
        username_lower = username if username else None

        player = {
            "_id": player_id,
            "username": username,
            "username_lower": username_lower,
            "updated_on": datetime.utcnow()
        }

        self.db.player.update(player)

    def player_get_by_id(self, player_id):
        player = self.db.player.find_one({"_id": as_objectid(player_id)})
        if player is None:
            raise PangeaException(PangaeaDealerErrorCodes.NotFoundError, "Player not found")

        return Player().from_dict(player)

    def player_get_by_username(self, username):
        if username:
            username = username.lower()

        player = self.db.player.find_one({"username_lower": username})
        if player is None:
            raise PangeaException(PangaeaDealerErrorCodes.NotFoundError, "Player not found")

        return player

    def player_username_exists(self, username):
        if username:
            username = username.lower()

        player = self.db.player.find_one({"username_lower": username})
        return player is not None

    def player_get_by_table_id(self, table_id):
        players = []

        table = self.db.table.find_one({"_id": as_objectid(table_id)}, {"seats"})
        if table and "seats" in table:
            player_ids = []
            for item in table["seats"]:
                if "player_id" in item:
                    player_id = as_objectid(item["player_id"])
                    player_ids.append(player_id)

            results = list(self.db.player.find({"_id": {"$in": player_ids}}))

            for document in results:
                players.append(Player().from_db(document))
        return players

    def player_get_all(self):
        results = list(self.db.player.find({}))

        players = []
        for document in results:
            players.append(Player.from_db(document))
        return players

    def player_join_table(self, table_id, player_id, username, seat_number, stack, playing):
        table_id = as_objectid(table_id)
        player_id = as_objectid(player_id)

        seat = {
            "_id": ObjectId(),
            "player_id": player_id,
            "username": username,
            "seat_number": seat_number,
            "stack": stack,
            "playing": playing
        }

        self.db.table.update({"_id": table_id}, {"$push": {"seats": seat}})
        self.table_set_updated(table_id)

        return Seat().from_dict(seat)

    def player_leave_table(self, table_id, player_id):
        table_id = as_objectid(table_id)
        player_id = as_objectid(player_id)

        self.db.table.update({"_id": table_id}, {"$pull": {"seats": {"player_id": player_id}}})
        self.table_set_updated(table_id)

    def player_set_bet(self, table_id, player_id, amount):
        table_id = as_objectid(table_id)
        player_id = as_objectid(player_id)

        self.db.table.update({"_id": table_id, "seats.player_id": player_id},
                             {"$set": {"seats.bet": amount}})
        self.table_set_updated(table_id)

    def player_fold(self, table_id, player_id):
        table_id = as_objectid(table_id)
        player_id = as_objectid(player_id)

        self.db.table.update({"_id": table_id, "seats.player_id": player_id},
                             {"$set": {"seats.playing": False}})
        self.table_set_updated(table_id)

    def player_update_stack(self, table_id, player_id, amount):
        table_id = as_objectid(table_id)
        player_id = as_objectid(player_id)
        self.db.table.update({"_id": table_id, "seats.player_id": player_id}, {"inc": {"seats.stack": amount}})

    # -- Events -- #
    def event_create(self, event_name, table_id, seat_number, player_name, bet=None):
        event = {
            "event_name": event_name,
            "table_id": as_objectid(table_id),
            "seat_number": seat_number,
            "player_name": player_name
        }

        if bet is not None:
            event["bet"] = bet

        self.db.event.insert(event)
        return TableEvent().from_dict(event)

    def event_remove(self, event_id):
        self.db.event.remove({"_id": as_objectid(event_id)})

    def event_get_by_table_id(self, table_id, since_date):
        if since_date:
            # Create a dummy event id which is then used to ensure that only
            # events which were created after the since date are returned
            query_event_id = ObjectId.from_datetime(since_date)
            query = self.db.event.find({"table_id": as_objectid(table_id), "_id": {"$gt": query_event_id}})
        else:
            query = self.db.event.find({"table_id": as_objectid(table_id)})

        results = list(query.sort("_id", 1).limit(50))

        events = []
        for document in results:
            events.append(TableEvent().from_db(document))
        return events

    # -- Chat messages -- #
    def chat_create(self, message, table_id):
        chat = {"message": message, "table_id": table_id}
        self.db.chat.insert(chat)
        return ChatMessage().from_dict(chat)

    def chat_get_by_table_id(self, table_id, since_date):

        if since_date:
            # Create a dummy chat id which is then used to ensure that only
            # chats which were created after the since date are returned
            query_chat_id = ObjectId.from_datetime(since_date)
            query = self.db.chat.find({"table_id": as_objectid(table_id), "_id": {"$gt": query_chat_id}})
        else:
            query = self.db.chat.find({"table_id": as_objectid(table_id)})

        results = list(query.sort("_id", 1).limit(100))

        chats = []
        for document in results:
            chats.append(ChatMessage().from_db(document))
        return chats

    # -- Bet -- #
    def bet_create(self, table_id, player_id, amount):
        bet = {"table_id": table_id, "player_id": player_id, "amount": amount}
        self.db.bet.insert(bet)
        return Bet().from_dict(bet)