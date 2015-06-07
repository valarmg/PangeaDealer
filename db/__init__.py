import os
import logging
from pymongo import MongoClient
from bson import ObjectId
from utils.errors import PangeaException, PangaeaDealerErrorCodes
from models import *
import utils


class PangeaDb(object):
    def __init__(self):
        self.log = logging.getLogger(__name__)

        if "OPENSHIFT_MONGODB_DB_URL" in os.environ:
            self.client = MongoClient(os.environ["OPENSHIFT_MONGODB_DB_URL"])
            self.log.debug("Created connection to Open Shift database")
        else:
            self.client = MongoClient("localhost", 27017)
            self.log.debug("Created connection to local database")

        self.lobby = LobbyRepo(self.client)
        self.table = TableRepo(self.client)
        self.player = PlayerRepo(self.client)
        self.event = EventRepo(self.client)
        self.chat = ChatRepo(self.client)


class LobbyRepo(object):
    def __init__(self, client):
        self.db = client.pangea

    def create(self, name, default=False):
        lobby = {"name": name, "default": default}
        self.db.lobby.insert(lobby)

        return Lobby().from_dict(lobby)

    def update(self, lobby: Lobby):
        self.db.lobby.update({"_id": utils.as_object_id(lobby.id)}, lobby.to_document())

    def delete(self, lobby_id):
        lobby_id = utils.as_object_id(lobby_id)
        self.db.lobby.remove({"_id": lobby_id})

    def delete_all(self):
        self.db.lobby.remove({})

    def get_by_id(self, lobby_id):
        lobby = self.db.lobby.find_one({"_id": utils.as_object_id(lobby_id)})
        if lobby is None:
            raise PangeaException(PangaeaDealerErrorCodes.NotFoundError, "Lobby not found")
        return Lobby.from_db(lobby)

    def get_all(self):
        results = list(self.db.lobby.find())

        lobbies = []
        for document in results:
            lobbies.append(Lobby().from_db(document))
        return lobbies

    def get_default(self):
        lobby = self.db.lobby.find_one({"default": True})
        if lobby:
            return Lobby().from_db(lobby)
        return None


class TableRepo(object):
    def __init__(self, client):
        self.db = client.pangea

    def create(self, lobby_id, name, default=False):
        lobby_id = utils.as_object_id(lobby_id)

        table = {
            "lobby_id": lobby_id,
            "name": name,
            "default": default,
            "updated_on": datetime.datetime.utcnow(),
            "big_blind": Table.DEFAULT_BIG_BLIND,
            "small_blind": Table.DEFAULT_SMALL_BLIND
        }

        table_id = self.db.table.insert(table)
        self.db.lobby.update({"_id": lobby_id}, {"$push": {"tables": table_id}})

        return Table().from_dict(table)

    def update(self, table):
        table.updated_on = datetime.datetime.utcnow()
        doc = table.to_document()
        self.db.table.update({"_id": utils.as_object_id(table.id)}, doc)

    def get_by_id(self, table_id):
        table = self.db.table.find_one({"_id": utils.as_object_id(table_id)})

        if table is None:
            raise PangeaException(PangaeaDealerErrorCodes.NotFoundError, "Table not found")
        return Table().from_db(table)

    def get_all(self):
        results = list(self.db.table.find())

        tables = []
        for document in results:
            tables.append(Table().from_db(document))
        return tables

    def get_all_with_timer(self):
        results = list(self.db.table.find({"turn_time_start": {"$ne": None}}))

        tables = []
        for document in results:
            tables.append(Table().from_db(document))
        return tables

    def get_default(self):
        table = self.db.table.find_one({"default": True})
        if table:
            return Table().from_db(table)
        return None

    def has_seat_timed_out(self, table: Table, seat_number):
        # Must do a database call to ensure the timeout hasn't occurred since the table data was retrieved from database
        # The seat is considered timed out if the seat has changed or the turn timer started less than 10 seconds ago

        max_start_time = datetime.datetime.utcnow() - datetime.timedelta(0, table.TURN_DURATION_IN_SECONDS)
        # * Not timed out example *
        # Current time: 10:40:00
        # Max start time: 10:10:00
        # Turn time start: 10:20:00

        # * Timed out example *
        # Current time: 10:40:00
        # Max start time: 10:10:00
        # Turn time start: 10:00:00

        result = self.db.table.find({"_id": utils.as_object_id(table.id), "current_seat_number": seat_number,
                                     "turn_time_start": {"$gt": max_start_time}}, {"_id": 1}).limit(1)

        # If we don't find a record then either the timer has just elapsed or the
        # player has been kicked and another player is the active
        return result is not None

    def delete(self, table_id):
        table_id = utils.as_object_id(table_id)
        table = self.db.table.find_one({"_id": table_id})

        if table is not None:
            self.db.lobby.update({"_id": table.lobby_id}, {"pull": {"tables": table_id}})
            self.db.lobby.update({"_id": table.lobby_id}, {"set": {"updated_on": datetime.datetime.utcnow()}})
            self.db.table.remove({"_id": table_id})
            self.db.event.remove({"table_id", table_id})

    def delete_all(self):
        self.db.table.remove({})


class PlayerRepo(object):
    def __init__(self, client):
        self.db = client.pangea

    def create(self, username):
        username_lower = username if username else None

        player = {
            "username": username,
            "username_lower": username_lower,
            "updated_on": datetime.datetime.utcnow()
        }

        self.db.player.insert(player)
        return Player().from_dict(player)

    def update(self, player: Player):
        self.db.player.update({"_id", utils.as_object_id(player.id)}, player.to_document())

    def get_by_id(self, player_id):
        player = self.db.player.find_one({"_id": utils.as_object_id(player_id)})
        if player is None:
            raise PangeaException(PangaeaDealerErrorCodes.NotFoundError, "Player not found")

        return Player().from_dict(player)

    def get_by_table_id(self, table_id):
        players = []

        table = self.db.table.find_one({"_id": utils.as_object_id(table_id)}, {"seats"})
        if table and "seats" in table:
            player_ids = []
            for item in table["seats"]:
                if "player_id" in item:
                    player_id = utils.as_object_id(item["player_id"])
                    player_ids.append(player_id)

            results = list(self.db.player.find({"_id": {"$in": player_ids}}))

            for document in results:
                players.append(Player().from_db(document))
        return players

    def get_all(self):
        results = list(self.db.player.find({}))

        players = []
        for document in results:
            players.append(Player.from_db(document))
        return players

    def delete(self, player_id):
        self.db.player.remove({"_id", utils.as_object_id(player_id)})

    def delete_all(self):
        self.db.player.remove({})


class EventRepo(object):
    def __init__(self, client):
        self.db = client.pangea

    def create(self, event_name, table_id, seat_number=None, player_name=None, bet=None):
        event = {
            "event_name": event_name,
            "table_id": utils.as_object_id(table_id),
            "seat_number": seat_number,
            "player_name": player_name
        }

        if bet is not None:
            event["bet"] = bet

        self.db.event.insert(event)
        return TableEvent().from_dict(event)

    def remove(self, event_id):
        self.db.event.remove({"_id": utils.as_object_id(event_id)})

    def get_by_table_id(self, table_id, since_date):
        table_id = utils.as_object_id(table_id)

        if since_date:
            # Create a dummy event id which is then used to ensure that only
            # events which were created after the since date are returned
            query_event_id = ObjectId.from_datetime(since_date)
            query = self.db.event.find({"table_id": table_id, "_id": {"$gt": query_event_id}})
        else:
            query = self.db.event.find({"table_id": table_id})

        results = list(query.sort("_id", 1).limit(20))

        events = []
        for document in results:
            events.append(TableEvent().from_db(document))
        return events


class ChatRepo(object):
    def __init__(self, client):
        self.db = client.pangea

    def create(self, message, table_id):
        chat = {"message": message, "table_id": table_id}
        self.db.chat.insert(chat)
        return ChatMessage().from_dict(chat)

    def get_by_table_id(self, table_id, since_date):
        table_id = utils.as_object_id(table_id)

        if since_date:
            # Create a dummy chat id which is then used to ensure that only
            # chats which were created after the since date are returned
            query_chat_id = ObjectId.from_datetime(since_date)
            query = self.db.chat.find({"table_id": table_id, "_id": {"$gt": query_chat_id}})
        else:
            query = self.db.chat.find({"table_id": table_id})

        results = list(query.sort("_id", 1).limit(100))

        chats = []
        for document in results:
            chats.append(ChatMessage().from_db(document))
        return chats