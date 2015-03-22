import os
from pymongo import MongoClient
from bson import ObjectId
from utils.errors import PangeaException, PangaeaDealerErrorCodes
from datetime import datetime

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
        if "OPENSHIFT_MONGODB_DB_URL" in os.environ:
            self.client = MongoClient(os.environ["OPENSHIFT_MONGODB_DB_URL"])
        else:
            self.client = MongoClient("localhost", 27017)

        self.db = self.client.pangea

    # -- Lobby -- #
    def lobby_create(self, lobby):
        lobby["updated_on"] = datetime.utcnow()
        self.db.lobby.insert(lobby)

    def lobby_update(self, lobby):
        lobby["updated_on"] = datetime.utcnow()
        lobby_id = get_id(lobby)

        self.db.lobby.update({"_id": lobby_id}, lobby)

    def lobby_delete(self, lobby_id):
        self.db.lobby.remove({"_id": lobby_id})

    def lobby_delete_all(self):
        self.db.lobby.remove({})

    def lobby_get_by_id(self, lobby_id):
        lobby = self.db.lobby.find_one({"_id": as_objectid(lobby_id)})
        if lobby is None:
            raise PangeaException(PangaeaDealerErrorCodes.NotFoundError, "Lobby not found")
        return lobby

    def lobby_get_all(self):
        return list(self.db.lobby.find())

    # -- Table -- #
    def table_create(self, table):
        lobby_id = as_objectid(table["lobby_id"])
        table["lobby_id"] = lobby_id
        table["updated_on"] = datetime.utcnow()

        table_id = self.db.table.insert(table)
        self.db.lobby.update({"_id": lobby_id}, {"$push": {"tables": table_id}})

    def table_update(self, table):
        table["updated_on"] = datetime.utcnow()
        self.db.table.update(table)

    def table_remove(self, table_id):
        table_id = as_objectid(table_id)
        table = self.db.table.find_one({"_id": table_id})

        if table is not None:
            self.db.lobby.update({"_id": as_objectid(table.lobby_id)}, {"pull": {"tables": table_id}})
            self.db.table.remove({"_id": table_id})
            self.db.event.remove({"table_id", table_id})

    def table_get_by_id(self, table_id):
        table = self.db.table.find_one({"_id": as_objectid(table_id)})
        if table is None:
            raise PangeaException(PangaeaDealerErrorCodes.NotFoundError, "Table not found")
        return table

    def table_get_by_lobby_id(self, lobby_id):
        return list(self.db.table.find({"lobby_id": as_objectid(lobby_id)}))

    def table_get_all(self):
        return list(self.db.table.find())

    # --  Player -- #
    def player_create(self, player):
        if "username" in player:
            player["username_lower"] = player["username"].lower()

        self.db.player.insert(player)

    def player_update(self, player):
        if "username" in player:
            player["username_lower"] = player["username"].lower()

        self.db.player.update(player)

    def player_get_by_id(self, player_id):
        player = self.db.player.find_one({"_id": as_objectid(player_id)})
        if player is None:
            raise PangeaException(PangaeaDealerErrorCodes.NotFoundError, "Player not found")

        return player

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
        player_ids = self.db.table.find_one({"_id": as_objectid(table_id)}).players
        return self.db.player.find({"_id": player_ids})

    def player_join_table(self, table_id, player_id, username, seat_number, stack):
        seat = {"player_id": player_id, "username": username, "seat_number": seat_number, "stack": stack}
        self.db.table.update({"_id": as_objectid(table_id)}, {"$push": {"seats": seat}})
        return seat

    def player_leave_table(self, table_id, player_id):
        self.db.table.update({"_id": as_objectid(table_id)},
                             {"$pull": {"seats": {"player_id": as_objectid(player_id)}}})

    # -- Events -- #
    def event_create(self, event_name, table_id, player_id, player_name):
        event = {
            "event_name": event_name,
            "table_id": table_id,
            "player_id": player_id,
            "player_name": player_name
        }

        self.db.event.insert(event)
        return event

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

        query = query.sort("_id", 1).limit(10)

        return list(query)

    # -- Chat messages -- #
    def chat_create(self, message, table_id):
        chat = {"message": message, "table_id": table_id}
        self.db.chat.insert(chat)
        return chat

    def chat_get_by_table_id(self, table_id, since_date):

        if since_date:
            # Create a dummy chat id which is then used to ensure that only
            # chats which were created after the since date are returned
            query_chat_id = ObjectId.from_datetime(since_date)
            query = self.db.chat.find({"table_id": as_objectid(table_id), "_id": {"$gt": query_chat_id}})
        else:
            query = self.db.chat.find({"table_id": as_objectid(table_id)})

        query = query.sort("_id", 1).limit(100)

        return list(query)

    # -- Bet -- #
    def bet_create(self, table_id, player_id, amount):
        bet = {"table_id": table_id, "player_id": player_id, "amount": amount}
        self.db.bet.insert(bet)
        return bet




