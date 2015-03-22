import json
from utils import PangeaJsonEncoder
from enum import Enum


def remove_nulls(obj):
    # TODO: Probably need to check for nulls in any sub dictionaries?
    return dict((k, v) for k, v in obj.items() if v is not None)


class Round(Enum):
    PreFlop = 1
    Flop = 2
    Turn = 3
    River = 4


class ModelBase(object):
    id = None

    def to_dict(self):
        return {}

    def from_dict(self, data):
        for key in data:
            if key == "_id" and hasattr(self, "id"):
                setattr(self, "id", data[key])
            elif hasattr(self, key):
                setattr(self, key, data[key])

    def to_json(self):
        result = self.to_dict()
        result = remove_nulls(result)
        return json.dumps(result, cls=PangeaJsonEncoder)


class Lobby(ModelBase):
    name = None
    tables = []

    @staticmethod
    def from_db(document):
        lobby = Lobby()
        lobby.id = document.get("_id")
        lobby.name = document.get("name")
        lobby.tables = document.get("tables")
        return lobby

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Table(ModelBase):
    name = None
    seats = []
    dealer_seat_number = None
    current_round = None
    board_cards = []
    deck_cards = []

    @staticmethod
    def from_db(document):
        model = Table()

        model.id = document.get("_id")
        model.name = document.get("name")
        model.dealer_seat_number = document.get("dealer_seat_number")
        model.current_round = document.get("current_round")
        model.board_cards = document.get("board_cards")
        model.deck_cards = document.get("deck_cards")

        seat_documents = document.get("seats", list())
        for document in seat_documents:
            seat_model = Seat.from_db(document)
            model.seats.append(seat_model)

        return model

    def to_dict(self):
        result = {
            "id": self.id,
            "name": self.name,
            "dealer_seat_number": self.dealer_seat_number,
            "current_round": self.current_round,
            "seats": [x.to_dict() for x in self.seats],
            "board_cards": self.board_cards,
            "deck_cards": self.deck_cards
        }
        return remove_nulls(result)


class Player(ModelBase):
    username = None

    @staticmethod
    def from_db(document):
        model = Player()
        model.id = document.get("_id")
        model.username = document.get("username")
        return model

    def to_dict(self):
        result = {
            "id": self.id,
            "username": self.username
        }
        return result


class Seat(ModelBase):
    player_id = None
    seat_number = None
    username = None
    stack = None
    hole_cards = []

    @staticmethod
    def from_db(document):
        model = Seat()
        model.seat_number = document.get("seat_number")
        model.player_id = document.get("player_id")
        model.username = document.get("username")
        model.stack = document.get("stack")
        model.hole_cards = document.get("hole_cards")
        return model

    def to_dict(self):
        result = {
            "seat_number": self.seat_number,
            "player_id": self.player_id,
            "username": self.username,
            "stack": self.stack,
            "hole_cards": self.hole_cards
        }
        return remove_nulls(result)


class ChatMessage(ModelBase):
    PLAYER_TABLE_JOIN = "Player {0} has joined the table"
    PLAYER_TABLE_LEAVE = "Player {0} has left the table"
    PLAYER_BET = "Player {0} has bet {1}"

    message = None
    player_name = None

    def __init__(self, message=None, player_name=None):
        self.message = message
        self.player_name = player_name

    @staticmethod
    def from_db_list(documents):
        models = []
        for document in documents:
            model = ChatMessage.from_db(document)
            models.append(model)

        return models

    @staticmethod
    def from_db(document):
        model = ChatMessage()
        model.id = document.get("_id")
        model.message = document.get("message")
        model.player_name = document.get("player_name")
        return model

    def to_dict(self):
        result = {
            "id": self.id,
            "message": self.message,
            "player_name": self.player_name
        }
        return result


class TableEvent(ModelBase):
    PLAYER_JOIN_TABLE = "player_join"
    PLAYER_LEAVE_TABLE = "player_leave"
    PLAYER_BET = "player_bet"

    event_name = None
    table_id = None
    player_id = None

    @staticmethod
    def from_db_list(documents):
        models = []
        for document in documents:
            model = TableEvent.from_db(document)
            models.append(model)

        return models

    @staticmethod
    def from_db(document):
        model = TableEvent()
        model.id = document.get("_id")
        model.name = document.get("event_name")
        model.table_id = document.get("table_id")
        model.player_id = document.get("player_id")
        return model

    def to_dict(self):
        result = {
            "id": self.id,
            "event_name": self.name,
            "table_id": self.table_id,
            "player_id": self.player_id
        }
        return result


class Bet(ModelBase):
    table_id = None
    player_id = None
    amount = None

    @staticmethod
    def from_db(document):
        model = Bet()
        model.id = document.get("_id")
        model.table_id = document.get("table_id")
        model.player_id = document.get("player_id")
        model.amount = document.get("amount")

    def to_dict(self):
        result = {
            "id": self.id,
            "table_id": self.table_id,
            "player_Id": self.player_id,
            "amount": self.amount
        }
        return result