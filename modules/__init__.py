import logging
from utils.errors import *
from random import shuffle
from models import *
import datetime
from utils import HandRank
from db import PangeaDb
import traceback


class BettingModule(object):

    def __init__(self, db: PangeaDb):
        self.db = db
        self.log = logging.getLogger(__name__)

    def check_or_call(self, table: Table, player: Player):
        self.log.debug("check_or_call, table_id: {0}, player_id: {1}".format(table.id, player.id))

        player_seat = table.organised_seats.get_seat_by_player_id(player.id)
        active_player_seat = table.get_active_seat()

        if player_seat is None:
            raise PangeaException(PangaeaDealerErrorCodes.BettingError, "Player is not sitting on the table")
        if active_player_seat is None or player_seat.seat_number != active_player_seat.seat_number:
            raise PangeaException(PangaeaDealerErrorCodes.BettingError, "Cannot bet out of turn")
        if table.has_turn_expired():
            raise PangeaException(PangaeaDealerErrorCodes.BettingError, "The players turn has expired")

        min_bet = self.calculate_min_check_or_call(table)
        if min_bet > 0:
            player_seat.bet = min_bet
            player_seat.status = "<span>Call</span>"
            player_seat.stack = player_seat.get_stack() - min_bet
            table.pot = table.get_pot() + min_bet

            self.db.chat.create(ChatMessage.PLAYER_CALL.format(player.username), table.id)
            self.db.event.create(TableEvent.PLAYER_CALL, table.id, player_seat.seat_number, player.username)
        else:
            player_seat.status = "<span>Check</span>"

            self.db.chat.create(ChatMessage.PLAYER_CHECK.format(player.username), table.id)
            self.db.event.create(TableEvent.PLAYER_CHECK, table.id, player_seat.seat_number, player.username)

    def bet(self, table: Table, player: Player, bet):
        self.log.debug("bet, table_id: {0}, player_id: {1}, Bet: {2}".format(table.id, player.id, bet))

        player_seat = table.organised_seats.get_seat_by_player_id(player.id)
        active_player_seat = table.get_active_seat()

        if player_seat is None:
            raise PangeaException(PangaeaDealerErrorCodes.BettingError, "Player is not sitting on the table")
        if active_player_seat is None or player_seat.seat_number != active_player_seat.seat_number:
            self.log.debug("Cannot bet out of turn, active seat: {0}, player seat: {1}".format(
                active_player_seat.seat_number if active_player_seat else "", player_seat.seat_number))
            raise PangeaException(PangaeaDealerErrorCodes.BettingError, "Cannot bet out of turn")
        if table.has_turn_expired():
            raise PangeaException(PangaeaDealerErrorCodes.BettingError, "The players turn has expired")

        try:
            bet = int(bet)
        except ValueError:
            self.log.error("Invalid bet amount, bet: {0}, exception: {1}".format(bet, traceback.format_exc()))
            raise PangeaException(PangaeaDealerErrorCodes.InvalidArgumentError, "Invalid bet amount")

        total_bet = player_seat.get_bet() + bet

        min_bet = self.calculate_min_raise(table)
        if total_bet < min_bet:
            raise PangeaException(PangaeaDealerErrorCodes.BettingError,
                                  "The player must bet at least: {0}".format(min_bet))

        table.current_bet = total_bet
        table.pot = table.get_pot() + bet

        player_seat.bet = total_bet
        player_seat.stack = player_seat.get_stack() - bet
        player_seat.status = "<span>Bet<br/>{0}</span>".format(bet)

        self.db.chat.create(ChatMessage.PLAYER_BET.format(player.username, bet), table.id)
        self.db.event.create(TableEvent.PLAYER_BET, table.id, player_seat.seat_number, player.username, bet=bet)

        # If a player raises, then the round cannot end until everyone else either folds or calls the raise
        table.dealing_to_seat_number = player_seat.seat_number

    def fold(self, table: Table, player: Player):
        player_seat = table.organised_seats.get_seat_by_player_id(player.id)
        selected_player = table.get_active_seat()

        if player_seat is None:
            raise PangeaException(PangaeaDealerErrorCodes.BettingError, "Player is not sitting on the table")
        if selected_player is None or player_seat.seat_number != selected_player.seat_number:
            raise PangeaException(PangaeaDealerErrorCodes.BettingError, "Cannot fold out of turn")
        if table.has_turn_expired():
            raise PangeaException(PangaeaDealerErrorCodes.BettingError, "The players turn has expired")

        player_seat.playing = False
        player.status = "<span>Fold</span>"
        player.bet = 0

        self.db.chat.create(ChatMessage.PLAYER_FOLD.format(player_seat.username), table.id)
        self.db.event.create(TableEvent.PLAYER_FOLD.format(player_seat.username), table.id,
                             player_seat.username, player_seat.username)

    def calculate_min_check_or_call(self, table: Table):
        return table.get_current_bet()

    def calculate_min_raise(self, table: Table):
        current_bet = table.get_current_bet()

        # You can't raise if there is no current bet so it's actually just a normal bet
        if current_bet == 0:
            return table.get_big_blind()

        return current_bet


class DealerModule(object):

    def __init__(self, db: PangeaDb):
        self.db = db
        self.log = logging.getLogger(__name__)

    def continue_hand(self, table: Table):
        self.log.debug("continue_hand. table_id: {0}".format(table.id))

        player_seat = table.get_active_seat()
        dealing_to_seat = table.get_dealing_to_seat()

        if player_seat is None:
            raise PangeaException(PangaeaDealerErrorCodes.ServerError, "No player seat set")
        if dealing_to_seat is None:
            raise PangeaException(PangaeaDealerErrorCodes.ServerError, "No dealing to seat set")

        # Move to the next player unless we hit the last player in the round
        if player_seat.seat_number != dealing_to_seat.seat_number:
            self.log.debug("Moving the next player in the table")
            self.move_active_seat(table)
            return

        self.log.debug("Reached the last player in the hand")

        # Everyone must have met the current bet before we can end the hand
        for seat in table.organised_seats.get_playing_seats():
            if seat.get_bet() < table.get_current_bet():
                self.log.debug("No everyone has meet the bet, moving around the table again")
                self.move_active_seat(table)
                return

        # Move to the next round, unless we are already on the last round
        if table.get_current_round() == Round.River:
            self.log.debug("The current round is the River, so the game is now over")
            self.end_hand(table)
            return

        table.current_round = table.get_current_round() + 1
        self.deal(table)

    def kick_timed_out_players(self, table: Table):
        require_update = False

        if table.get_current_round() == Round.NA:
            return

        if table.has_turn_expired():
            player_seat = table.get_active_seat()
            if player_seat:
                self.log.debug(("Kicking out player due to timeout, seat_number: {0}, current_time " +
                                "(UTC): {1}, turn_time_start (UTC): {2}")
                               .format(player_seat.seat_number, datetime.datetime.utcnow(), table.turn_time_start))

                self.move_active_seat(table)
                self.remove_seat(table, player_seat)

                self.db.chat.create(ChatMessage.PLAYER_TIMEOUT.format(player_seat.username), table.id)
                self.db.event.create(TableEvent.PLAYER_LEAVE_TABLE.format(player_seat.username), table.id,
                                     player_seat.seat_number, player_seat.username)
                require_update = True

        # Stop the hand if there is only one player left
        if not self.has_table_enough_players(table):
            self.end_hand(table)
            require_update = True

        return require_update

    def restart_table(self, table: Table):
        require_update = False

        if table.get_current_round() == Round.NA and self.has_table_enough_players(table):
            self.start_hand(table)
            require_update = True

        return require_update

    def join_table(self, table: Table, player: Player, seat_number, stack):
        self.log.debug("join_table, table_id: {0}, player_id: {1}".format(table.id, player.id))

        exists = table.seats and any(x.seat_number == seat_number for x in table.seats)
        if exists:
            raise PangeaException(PangaeaDealerErrorCodes.AlreadyExists, "Seat was been taken by another player")

        playing = True if table.get_current_round() == Round.NA else False
        seat = Seat(player_id=player.id, seat_number=seat_number,
                    username=player.username, stack=stack, playing=playing)
        table.add_seat(seat)

        self.db.chat.create(ChatMessage.PLAYER_TABLE_JOIN.format(player.username), table.id)
        self.db.event.create(TableEvent.PLAYER_JOIN_TABLE, table.id, seat_number, player.username)

        # Start the hand if a second player joins the table
        current_round = table.get_current_round()
        if self.has_table_enough_players(table) and current_round == Round.NA:
            self.log.debug("There are enough to start the hand")
            self.start_hand(table)

    def leave_table(self, table: Table, player: Player):
        self.log.debug("leave_table, table_id: {0}, player_id: {1}".format(table.id, player.id))

        player_seat = table.organised_seats.get_seat_by_player_id(player.id)
        if player_seat is None:
            raise PangeaException(PangaeaDealerErrorCodes.NotFoundError, "Player is not sitting on the table")

        self.remove_seat(table, player_seat)

        self.db.chat.create(ChatMessage.PLAYER_TIMEOUT.format(player_seat.username), table.id)
        self.db.event.create(TableEvent.PLAYER_LEAVE_TABLE.format(player_seat.username), table.id,
                             player_seat.seat_number, player_seat.username)

    def start_hand(self, table: Table):
        if self.has_table_enough_players(table) and table.get_current_round() == Round.NA:
            self.log.debug("There are two or more players, starting the hand")
            table.current_round = Round.PreFlop
            self.deal(table)
        else:
            self.log.debug("Cannot start a new hand. Either there are not enough players, or "
                           + "the hand is already in progress")

    def end_hand(self, table: Table):
        self.log.debug("end_hand, table_id: {0}".format(table.id))

        if table.get_current_round() == Round.NA:
            table.end_hand()
            self.move_dealer_seat(table)
            self.db.chat.create(ChatMessage.DEAL_END, table.id)
            self.db.event.create(TableEvent.HAND_COMPLETE, table.id)
            return

        playing_seats = table.organised_seats.get_playing_seats()
        if len(playing_seats) == 0:
            winning_seat = None
        elif len(playing_seats) == 1:
            winning_seat = playing_seats[0]
        else:
            winning_seat = self.determine_table_winner(table)

        if winning_seat:
            self.log.debug("Winner seating, seat_number: {0}, pot: {1}"
                           .format(winning_seat.seat_number, table.get_pot()))
            winning_seat.stack = winning_seat.get_stack() + table.get_pot()

            for seat in playing_seats:
                cards = ",".join(seat.hole_cards) if seat.hole_cards else ""
                message = ChatMessage.PLAYER_CARD_FLIP.format(seat.username, cards)
                self.db.chat.create(message, table.id)

            message = ChatMessage.PLAYER_WIN.format(winning_seat.username, table.get_pot())
            self.db.chat.create(message, table.id)

            table.end_hand()
            self.move_dealer_seat(table)

        self.db.chat.create(ChatMessage.DEAL_END, table.id)
        self.db.event.create(TableEvent.HAND_COMPLETE, table.id)

    def has_table_enough_players(self, table: Table):
        playing_seats = table.organised_seats.get_playing_seats()
        return len(playing_seats) >= 2

    def remove_seat(self, table: Table, seat: Seat):
        if table.active_seat_number == seat.seat_number:
            self.move_active_seat(table)

        # TODO: Should probably only change the dealer seat if the before the preflop
        if table.dealing_to_seat_number == seat.seat_number:
            next_seat = table.organised_seats.get_next_seat(seat.seat_number)
            if next_seat:
                table.dealer_seat_number = next_seat.seat_number

        if table.dealer_seat_number == seat.seat_number:
            self.move_dealer_seat(table)

        table.remove_seat(seat)

        # Stop hand if there is only one player remaining
        if not self.has_table_enough_players(table):
            self.end_hand(table)

    def move_active_seat(self, table: Table):
        player_seat = table.get_active_seat()
        if player_seat is None:
            # If there is no active seat, the first seat should be the active
            player_seat = table.organised_seats.get_first_seat()
        else:
            # Otherwise get the next seat
            player_seat = table.organised_seats.get_next_seat(player_seat.seat_number)

        self.set_active_seat(table, player_seat)

    def set_active_seat(self, table: Table, seat: Seat):
        table.active_seat_number = seat.seat_number
        table.turn_time_start = datetime.datetime.utcnow()

        message = ChatMessage.PLAYER_TURN.format(seat.username)
        self.db.chat.create(message, table.id)

        self.log.debug("Set active seat, seat_number: {0}, turn_time_start: {1}"
                       .format(table.active_seat_number, table.turn_time_start))

    def move_dealer_seat(self, table: Table):
        dealer_seat = table.get_dealer_seat()
        if dealer_seat is None:
            # If there is no dealer, the first seat should be the dealer
            dealer_seat = table.organised_seats.get_first_seat()
        else:
            # Otherwise get the next seat
            dealer_seat = table.organised_seats.get_next_seat(dealer_seat.seat_number)

        if dealer_seat is None:
            table.dealer_seat_number = None
        else:
            table.dealer_seat_number = dealer_seat.seat_number

        self.log.debug("Moved dealer seat, seat_number: {0}".format(table.dealer_seat_number))

    def deal(self, table: Table):
        self.log.debug("deal, table_id: {0}".format(table.id))

        if not self.has_table_enough_players(table):
            self.log.debug("Cannot deal when there are less than 2 players in the hand")
            return

        table.current_bet = 0
        current_round = table.get_current_round()
        table.clear_seat_bets_statuses()

        if current_round == Round.PreFlop:
            self.deal_preflop(table)
        elif current_round == Round.Flop:
            self.deal_flop(table)
        elif current_round == Round.Turn:
            self.deal_turn(table)
        elif current_round == Round.River:
            self.deal_river(table)
        else:
            self.log.error("Cannot deal when the round is NA")
            return

        # In the preflop, the first person to bet is the person to the left of the big blind
        # In other rounds, the first person to act is the person to the left of the dealer
        if current_round == Round.PreFlop:
            big_blind_seat = table.get_big_blind_seat()
            if not big_blind_seat:
                raise PangeaException(PangaeaDealerErrorCodes.ServerError, "No big blind was found")
            seat = table.organised_seats.get_next_seat(big_blind_seat.seat_number)
            self.set_active_seat(table, seat)
        else:
            seat = table.organised_seats.get_next_seat(table.dealer_seat_number)
            self.set_active_seat(table, seat)

        # Everyone in the hand must be allowed to bet. So the last person in the hand
        # must be sitting to the right of the first person to bet
        dealing_to_seat = table.organised_seats.get_previous_seat(table.active_seat_number)
        table.dealer_seat_number = dealing_to_seat.seat_number
        table.dealing_to_seat_number = dealing_to_seat.seat_number

    def deal_preflop(self, table: Table):
        self.log.debug("deal_preflop, table_id: {0}, current_round: {1}".format(table.id, table.current_round))

        table.flip_cards = False
        for seat in table.seats:
            seat.flipped_cards = None

        # Make sure that a dealer has been set
        if table.dealer_seat_number is None:
            seat = table.organised_seats.get_first_seat()
            if seat is None:
                self.log.debug("Cannot deal a preflop if there are no playing players")
                return

            table.dealer_seat_number = seat.seat_number

        # Create a deck
        table.deck_cards = self.create_deck()

        # Give each player cards
        for seat in table.seats:
            cards = self.deal_cards_from_deck(table.deck_cards, 2)
            seat.hole_cards = cards

        # Set blinds
        table.current_bet = table.get_big_blind()
        table.get_big_blind_seat().current_bet = table.get_big_blind()
        table.get_small_blind_seat().current_bet = table.get_small_blind()

        self.db.chat.create(ChatMessage.DEAL_PREFLOP, table.id)

    def deal_flop(self, table: Table):
        self.log.debug("deal_flop, table_id: {0}".format(table.id))

        # Deal the board cards
        table.board_cards = self.deal_cards_from_deck(table.deck_cards, 3)

        message = ChatMessage.DEAL_FLOP.format(",".join(table.board_cards))
        self.db.chat.create(message, table.id)

    def deal_turn(self, table):
        self.log.debug("deal_turn, table_id: {0}".format(table.id))

        # Deal the board cards
        if not table.board_cards:
            raise PangeaException(PangaeaDealerErrorCodes.ServerError,
                                  "Trying to deal the turn but no other cards have been dealt yet")

        turn_card = self.deal_cards_from_deck(table.deck_cards, 1)[0]
        table.board_cards.append(turn_card)

        self.db.chat.create(ChatMessage.DEAL_TURN.format(turn_card), table.id)

    def deal_river(self, table):
        self.log.debug("deal_river, table_id: {0}".format(table.id))

        # Deal the board cards
        if not table.board_cards:
            raise PangeaException(PangaeaDealerErrorCodes.ServerError,
                                  "Trying to deal the river but no other cards have been dealt yet")

        river_card = self.deal_cards_from_deck(table.deck_cards, 1)[0]
        table.board_cards.append(river_card)

        self.db.chat.create(ChatMessage.DEAL_RIVER.format(river_card), table.id)

    def determine_table_winner(self, table: Table):
        seats = table.organised_seats.get_playing_seats()

        winning_seat = None
        winning_score = 0

        # Flip the cards so players will know why they won or lost
        table.flip_cards = True
        for seat in table.seats:
            if seat.playing:
                seat.flipped_cards = seat.hole_cards

        for seat in seats:
            hand_rank_str, score = HandRank.evaluate_hand(table.board_cards, seat.hole_cards)
            self.log.debug("hand_rank_str: {0}, score: {1}".format(hand_rank_str, score))

            if winning_seat is None or score > winning_score:
                winning_score = score
                winning_seat = seat

        return winning_seat

    def create_deck(self):
        # TODO: Not sure if this is random enough
        cards = list(range(0, 51))
        shuffle(cards)
        return cards

    def deal_cards_from_deck(self, deck, cards_to_deal):
        if deck is None:
            raise PangeaException(PangaeaDealerErrorCodes.ServerError, "Invalid deck")
        if len(deck) < cards_to_deal:
            raise PangeaException(PangaeaDealerErrorCodes.ServerError, "Not enough cards remaining in the deck")

        cards = []
        for i in range(cards_to_deal):
            card = self.convert_card_from_num(deck.pop())
            cards.append(card)

        return cards

    def convert_card_from_num(self, card_number):
        conversion_suit = ("h", "s", "d", "c")
        conversion_rank = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K")

        [suit, rank] = divmod(card_number, 13)
        suit1 = conversion_suit[suit]
        rank1 = conversion_rank[rank]

        return rank1 + suit1