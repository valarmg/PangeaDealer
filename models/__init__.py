import json
from utils import PangeaJsonEncoder
from enum import Enum


def remove_nulls(obj):
    return dict((k, v) for k, v in obj.items() if v is not None)


class Round(Enum):
    PreFlop = 1
    Flop = 2
    Turn = 3
    River = 4


class ModelBase(object):

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
    id = None
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
    id = None
    name = None
    seats = []
    dealer_seat_number = None
    current_round = None
    table_cards = []
    deck_cards = []

    @staticmethod
    def from_db(document):
        model = Table()

        model.id = document.get("_id")
        model.name = document.get("name")
        model.dealer_seat_number = document.get("dealer_seat_number")
        model.current_round = document.get("current_round")
        model.table_cards = document.get("table_cards")
        model.deck_cards = document.get("deck_cards")

        seat_documents = document.get("seats", list())
        for document in seat_documents:
            seat_model = Seat.from_db(document)
            model.seats.append(seat_model)

        return model

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "dealer_seat_number": self. dealer_seat_number,
            "current_round": self.current_round,
            "seats": [x.to_dict() for x in self.seats],
            "table_cards": self.table_cards,
            "deck_cards": self.deck_cards
        }


class Seat(ModelBase):
    seat_number = None
    player_id = None
    player_name = None
    stack = None
    cards = []

    def __init__(self, player_id=None, player_name=None, seat_number=None, stack=None, cards=[]):
        self.player_id = player_id
        self.player_name = player_name
        self.seat_number = seat_number
        self.stack = stack
        self.cards = cards

    @staticmethod
    def from_db(document):
        model = Seat()
        model.number = document.get("seat_number")
        model.player_id = document.get("player_id")
        model.player_name = document.get("player_name")
        model.stack = document.get("stack")
        model.cards = document.get("cards")
        return model

    def to_dict(self):
        return {
            "name": self.name,
            "seat_number": self.seat_number,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "stack": self.stack,
            "cards": self.cards
        }