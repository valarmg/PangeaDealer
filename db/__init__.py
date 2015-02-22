from pymongo import MongoClient
from bson import ObjectId
from utils.errors import PangeaException, PangaeaErrorCodes


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
        self.host = "localhost"
        self.port = 27017
        self.client = MongoClient(self.host, self.port)
        self.db = self.client.pangea

    # -- Lobby -- #
    def lobby_create(self, lobby):
        self.db.lobby.insert(lobby)

    def lobby_update(self, lobby):
        lobby_id = get_id(lobby)

        self.db.lobby.update({"_id": lobby_id}, lobby)

    def lobby_delete(self, lobby_id):
        self.db.lobby.remove({"_id": lobby_id})

    def lobby_delete_all(self):
        self.db.lobby.remove({})

    def lobby_get_by_id(self, lobby_id):
        lobby = self.db.lobby.find_one({"_id": as_objectid(lobby_id)})
        if lobby is None:
            raise PangeaException(PangaeaErrorCodes.NotFoundError, "Lobby not found")
        return lobby

    def lobby_get_all(self):
        return list(self.db.lobby.find())

    # -- Table -- #
    def table_create(self, table):
        lobby_id = as_objectid(table["lobby_id"])
        table["lobby_id"] = lobby_id

        table_id = self.db.table.insert(table)
        self.db.lobby.update({"_id": lobby_id}, {"$push": {"tables": table_id}})

    def table_update(self, table):
        self.db.table.update(table)

    def table_remove(self, table_id):
        table_id = as_objectid(table_id)
        table = self.db.table.find_one({"_id": table_id})

        if table is not None:
            self.db.lobby.update({"_id": as_objectid(table.lobby_id)}, {"pull": {"tables": table_id}})
            self.db.table.remove({"_id": table_id})

    def table_get_by_id(self, table_id):
        table = self.db.table.find_one({"_id": as_objectid(table_id)})
        if table is None:
            raise PangeaException(PangaeaErrorCodes.NotFoundError, "Table not found")
        return table

    def table_get_by_lobby_id(self, lobby_id):
        return list(self.db.table.find({"lobby_id": as_objectid(lobby_id)}))

    def table_get_all(self):
        return list(self.db.table.find())

    # --  Player -- #
    def player_create(self, player):
        self.db.player.insert(player)

    def player_update(self, player):
        self.db.player.update(player)

    def player_get_by_id(self, player_id):
        player = self.db.player.find_one({"_id": as_objectid(player_id)})
        if player is None:
            raise PangeaException(PangaeaErrorCodes.NotFoundError, "Player not found")
        return player

    def player_get_by_table_id(self, table_id):
        player_ids = self.db.table.find_one({"_id": as_objectid(table_id)}).players
        return self.db.player.find({"_id": player_ids})

    def player_join_table(self, table_id, seat):
        seat["player_id"] = as_objectid(seat["player_id"])
        self.db.table.update({"_id": as_objectid(table_id)}, {"$push": {"seats": seat}})

    def player_leave_table(self, table_id, player_id):
        self.db.table.update({"_id": as_objectid(table_id)},
                             {"$pull": {"seats": {"player_id": as_objectid(player_id)}}})