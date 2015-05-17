from models import *
import logging
from utils.errors import *


class BetModule(object):
    logger = logging.getLogger(__name__)

    def __init__(self, db):
        self.db = db

    def check(self, table: Table, player: Player):
        player_seat = table.organised_seats.get_seat_by_player_id(player.id)
        selected_player = table.get_player_seat()

        if player_seat is None:
            raise PangeaException(PangaeaDealerErrorCodes.BettingError, "Player is not sitting on the table")
        if selected_player is None or player_seat.seat_number != selected_player.seat_number():
            raise PangeaException(PangaeaDealerErrorCodes.BettingError, "Not the players turn")

        self.validate_bet(table, player_seat.get_bet(), False)

        # Do bet
        self.db.chat_create(ChatMessage.PLAYER_CHECK.format(player.username), table.id)
        self.db.event_create(TableEvent.PLAYER_CHECK.format(player.username), table.id,
                             player_seat.seat_number, player.username)

    def bet(self, table: Table, player: Player, bet, is_raise):
        player_seat = table.organised_seats.get_seat_by_player_id(player.id)
        selected_player = table.get_player_seat()

        if player_seat is None:
            raise PangeaException(PangaeaDealerErrorCodes.BettingError, "Player is not sitting on the table")
        if selected_player is None or player_seat.seat_number != selected_player.seat_number():
            raise PangeaException(PangaeaDealerErrorCodes.BettingError, "Not the players turn")

        try:
            total_bet = player_seat.get_bet() + int(bet)
        except ValueError:
            raise PangeaException(PangaeaDealerErrorCodes.InvalidArgumentError, "Invalid bet amount")

        self.validate_bet(table, total_bet, is_raise)

        # Do bet
        self.db.bet(table.id, player.id, total_bet)
        self.db.chat_create(ChatMessage.PLAYER_BET.format(player.username), table.id)
        self.db.event_create(TableEvent.PLAYER_BET.format(player.username, bet), table.id,
                             player_seat.seat_number, player.username, bet=bet)

        # If a player raises, then the round cannot end until every else either folds or calls the raise
        if is_raise:
            table.dealing_to_seat_number = player_seat.seat_number
            self.db.table_set_dealer_seat(table.id, player_seat.seat_number)

    def fold(self, table: Table, player: Player):
        player_seat = table.organised_seats.get_seat_by_player_id(player.id)
        selected_player = table.get_player_seat()

        if player_seat is None:
            raise PangeaException(PangaeaDealerErrorCodes.BettingError, "Player is not sitting on the table")
        if selected_player is None or player_seat.seat_number != selected_player.seat_number():
            raise PangeaException(PangaeaDealerErrorCodes.BettingError, "Not the players turn")

        self.db.fold(table.id, player.id)
        self.db.chat_create(ChatMessage.PLAYER_FOLD.format(player.player_name), table.id)
        self.db.event_create(TableEvent.PLAYER_FOLD.format(player.player_name), table.id,
                             player.seat.seat_number, player.player_name)

    def validate_bet(self, table: Table, bet, is_raise):
        if is_raise:
            min_bet = self.calculate_min_raise(table)
        else:
            min_bet = self.calculate_min_check_or_call(table)

        if min_bet > bet:
            raise PangeaException(PangaeaDealerErrorCodes.BettingError,
                                  "The player must bet at least: {0}".format(min_bet))

    def calculate_min_check_or_call(self, table: Table):
        current_bet = table.get_current_bet()

        # The big blind is always the minimum
        if current_bet == 0:
            return table.get_big_blind()

        return current_bet

    def calculate_min_raise(self, table: Table):
        current_bet = table.get_current_bet()

        # You can't raise if there is no current bet so it's actually just a normal bet
        if current_bet == 0:
            return table.get_big_blind()

        return current_bet