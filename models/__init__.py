import json
from utils import PangeaJsonEncoder
import operator


def remove_nulls(obj):
    # TODO: Probably need to check for nulls in any sub dictionaries?
    return dict((k, v) for k, v in obj.items() if v is not None)


class Round():
    NA = 0
    PreFlop = 1
    Flop = 2
    Turn = 3
    River = 4


class ModelBase(object):

    def __init__(self):
        self.id = None

    def to_dict(self):
        return {"id": self.id}

    def from_dict(self, data):
        for key in data:
            if key == "_id" and hasattr(self, "id"):
                setattr(self, "id", data[key])
            elif hasattr(self, key):
                setattr(self, key, data[key])
        return self

    def from_db(self, document):
        self.id = document.get("_id")

    def to_json(self):
        result = self.to_dict()
        result = remove_nulls(result)
        return json.dumps(result, cls=PangeaJsonEncoder)


class Lobby(ModelBase):

    def __init__(self):
        super().__init__()
        self.name = None
        self.tables = []

    def from_db(self, document):
        super().from_db(document)
        self.name = document.get("name")
        self.tables = document.get("tables")
        return self

    def to_dict(self):
        result = {"id": self.id, "name": self.name}
        return remove_nulls(result)


class Table(ModelBase):

    def __init__(self):
        super().__init__()
        self.name = None
        self.seats = []
        self.dealer_seat_number = None
        self.player_seat_number = None
        self.current_round = None
        self.board_cards = None
        self.deck_cards = None
        self.small_blind = None
        self.big_blind = None
        self.organised_seats = None
        self.turn_time_start = None
        self.current_bet = None
        self.dealing_to_seat_number = None
        self.pot = None

    def from_db(self, document):
        super().from_db(document)

        self.name = document.get("name")
        self.dealer_seat_number = document.get("dealer_seat_number")
        self.player_seat_number = document.get("player_seat_number")
        self.current_round = document.get("current_round")
        self.board_cards = document.get("board_cards")
        self.deck_cards = document.get("deck_cards")
        self.small_blind = document.get("small_blind")
        self.big_blind = document.get("big_blind")
        self.turn_time_start = document.get("turn_time_start")
        self.current_bet = document.get("current_bet")
        self.dealing_to_seat_number = document.get("dealing_to_seat_number")
        self.pot = document.get("Pot")

        self.seats = []
        seat_documents = document.get("seats", list())
        for document in seat_documents:
            self.seats.append(Seat().from_db(document))

        self.organised_seats = OrganisedSeats(self.seats)

        return self

    def to_dict(self):
        result = {
            "id": self.id,
            "name": self.name,
            "dealer_seat_number": self.dealer_seat_number,
            "player_seat_number": self.player_seat_number,
            "current_round": self.current_round,
            "turn_time_start": self.turn_time_start,
            "seats": [x.to_dict() for x in self.seats],
            "board_cards": self.board_cards,
            "deck_cards": self.deck_cards,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "current_bet": self.current_bet,
            "dealing_to_seat_number": self.dealing_to_seat_number,
            "pot": self.pot
        }
        return remove_nulls(result)

    def get_dealer_seat(self, playing_only=True):
        if self.dealer_seat_number is None:
            return self.organised_seats.get_first_seat(playing_only)
        else:
            return self.organised_seats.get_seat(self.dealer_seat_number)

    def get_small_blind_seat(self, playing_only=True):
        dealer_seat = self.get_dealer_seat(playing_only)
        if dealer_seat is None:
            return None
        return self.organised_seats.get_next_seat(dealer_seat.seat_number)

    def get_big_blind_seat(self, playing_only=True):
        small_blind_seat = self.get_small_blind_seat(playing_only)
        if small_blind_seat is None:
            return None
        return self.organised_seats.get_next_seat(small_blind_seat.seat_number)

    def get_player_seat(self):
        if self.player_seat_number is None:
            return None
        return self.organised_seats.get_seat(self.dealer_seat_number)

    def get_dealing_to_seat(self):
        if self.dealing_to_seat_number is None:
            return None
        return self.organised_seats.get_seat(self.dealing_to_seat_number)

    def get_big_blind(self):
        return int(self.big_blind) if self.big_blind else 0

    def get_small_blind(self):
        return int(self.small_blind) if self.small_blind else 0

    def get_current_bet(self):
        return int(self.current_bet) if self.current_bet else 0

    def get_pot(self):
        return int(self.pot) if self.pot else 0

    def get_seat_numbers(self):
        for seat in self.seats:
            yield seat.seat_number


class Player(ModelBase):

    def __init__(self):
        super().__init__()
        self.username = None

    def from_db(self, document):
        super().from_db(document)
        self.username = document.get("username")
        return self

    def to_dict(self):
        result = {
            "id": self.id,
            "username": self.username
        }
        return remove_nulls(result)


class Seat(ModelBase):

    def __init__(self):
        super().__init__()
        self.player_id = None
        self.seat_number = None
        self.username = None
        self.stack = None
        self.hole_cards = []
        self.bet = None
        self.playing = None

    def from_db(self, document):
        super().from_db(document)
        self.seat_number = document.get("seat_number")
        self.player_id = document.get("player_id")
        self.username = document.get("username")
        self.stack = document.get("stack")
        self.hole_cards = document.get("hole_cards")
        self.bet = document.get("bet")
        self.playing = document.get("playing")
        return self

    def to_dict(self):
        result = {
            "id": self.id,
            "seat_number": self.seat_number,
            "player_id": self.player_id,
            "username": self.username,
            "stack": self.stack,
            "hole_cards": self.hole_cards,
            "bet": self.bet,
            "playing": self.playing
        }
        return remove_nulls(result)

    def get_bet(self):
        return int(self.bet) if self.bet else 0


class ChatMessage(ModelBase):
    PLAYER_TABLE_JOIN = "Player {0} has joined the table"
    PLAYER_TABLE_LEAVE = "Player {0} has left the table"
    PLAYER_BET = "Player {0} has bet {1}"
    PLAYER_CHECK = "Player {0} has checked"
    PLAYER_FOLD = "Player {0} has folded"
    PLAYER_TIMEOUT = "Player {0} has timed out"

    def __init__(self, message=None, player_name=None):
        super().__init__()
        self.message = message
        self.player_name = player_name

    def from_db(self, document):
        super().from_db(document)
        self.message = document.get("message")
        self.player_name = document.get("player_name")
        return self

    def to_dict(self):
        result = {
            "id": self.id,
            "message": self.message,
            "player_name": self.player_name
        }
        return remove_nulls(result)


class TableEvent(ModelBase):
    PLAYER_JOIN_TABLE = "player_join"
    PLAYER_LEAVE_TABLE = "player_leave"
    PLAYER_BET = "player_bet"
    PLAYER_CHECK = "player_check"
    PLAYER_FOLD = "player_fold"

    def __init__(self):
        super().__init__()
        self.event_name = None
        self.table_id = None
        self.seat_number = None
        self.bet = None

    def from_db(self, document):
        super().from_db(document)
        self.event_name = document.get("event_name")
        self.table_id = document.get("table_id")
        self.seat_number = document.get("seat_number")
        self.bet = document.get("bet")
        return self

    def to_dict(self):
        result = {
            "id": self.id,
            "event_name": self.event_name,
            "table_id": self.table_id,
            "seat_number": self.seat_number,
            "bet": self.bet
        }
        return remove_nulls(result)


class Bet(ModelBase):

    def __init__(self):
        super().__init__()
        self.table_id = None
        self.player_id = None
        self.amount = None

    def from_db(self, document):
        super().from_db(document)
        self.table_id = document.get("table_id")
        self.player_id = document.get("player_id")
        self.amount = document.get("amount")

    def to_dict(self):
        result = {
            "id": self.id,
            "table_id": self.table_id,
            "player_Id": self.player_id,
            "amount": self.amount
        }
        return remove_nulls(result)


class OrganisedSeats(object):
    def __init__(self, seats):
        self.seats = sorted(seats, key=lambda x: x.seat_number)
        self.seat_numbers = []

        for seat in self.seats:
            if seat.seat_number:
                self.seat_numbers.append(int(seat.seat_number))

    def get_first_seat(self, playing_only=True):
        seats = self.get_playing_seats() if playing_only else self.seats

        if len(seats) > 0:
            return seats[0]
        return None

    def get_next_seat(self, seat_number, playing_only=True):
        seats = self.get_playing_seats() if playing_only else self.seats

        for i in range(len(seats)):
            if seats[i].seat_number == seat_number:
                if len(seats) >= (i + 1):
                    return seats[i+1]
                else:
                    return seats[0]
        return None

    def get_seat(self, seat_number):
        for seat in self.seats:
            if seat.seat_number == seat_number:
                return seat
        return None

    def get_seat_by_player_id(self, player_id):
        for seat in self.seats:
            if seat.player_id and str(player_id) == str(seat.player_id):
                return seat
        return None

    def get_playing_seats(self):
        results = []
        for seat in self.seats:
            if seat.playing:
                results.append(seat)
        return results