from models import Table
from random import shuffle
import logging
from utils.errors import *
from models import *
import datetime
from utils import HandRank


class DealerModule(object):
    logger = logging.getLogger(__name__)

    def __init__(self, db):
        self.db = db

    def kick_timed_out_players(self, table: Table):
        self.logger.debug("kick_timed_out_players, table_id: {0}, turn_time_start: {1}"
                          .format(table.id, table.turn_time_start))

        if table.turn_time_start is None or table.current_round == Round.NA:
            return

        expiry = table.turn_time_start + datetime.timedelta(0, 30)

        if table.player_seat_number and expiry > datetime.datetime.utcnow():

            player_seat = table.get_player_seat()
            player = self.db.player_get_by_id(player_seat.player_id)

            self.db.player_leave_table(player_seat.player_id)
            self.db.chat_create(ChatMessage.PLAYER_TIMEOUT.format(player.player_name), table.id)
            self.db.event_create(TableEvent.PLAYER_LEAVE_TABLE.format(player.player_name), table.id,
                                 player_seat.seat_number, player.player_name)

    def continue_hand(self, table: Table):
        self.logger.debug("continue_hand, table_id: {0}".format(table.id))

        # If there are less than 2 people playing (1 player was kicked or left) then
        # automatically give the pot to the other player
        playing_seats = table.organised_seats.get_playing_seats()
        if len(playing_seats) < 2:
            self.logger.debug("Not enough players to play hand")
            self.db.table_reset_seats(table.id, table.get_seat_numbers())
            self.end_hand(table)
            return

        if table.current_round is None or table.current_round == Round.NA:
            # Start / restart the hand
            self.logger.debug("Starting a new hand")
            table.current_round = Round.PreFlop

            if table.dealer_seat_number is None:
                dealer_seat = table.organised_seats.get_first_seat()
                table.dealer_seat_number = dealer_seat.seat_number
                self.db.table_set_dealer_seat(table.id, dealer_seat.seat_number)

            self.deal(table)
            return

        player_seat = table.get_player_seat()
        dealing_to_seat = table.get_dealing_to_seat()

        if player_seat is None:
            raise PangeaException(PangaeaDealerErrorCodes.ServerError, "No player seat set")
        if dealing_to_seat is None:
            raise PangeaException(PangaeaDealerErrorCodes.ServerError, "No dealing to seat set")

        # The "dealing to" player is either the big blind on the preflop, the small blind on the
        # other rounds, or the last person who raised. The round ends once that person decided to check
        if player_seat.seat_number == dealing_to_seat.seat_number:
            self.logger.debug("Reached 'dealing to' player")
            if table.current_round == Round.River:
                self.end_hand(table)
                return

            if not table.current_round:
                table.current_round = Round.NA

            table.current_round += 1
            self.db.table_set_current_round(table.current_round)
            self.deal(table)
        else:
            self.move_player_seat(table)

    def end_hand(self, table: Table):
        self.logger.debug("end_hand, table_id: {0}".format(table.id))

        if table.current_round is None or table.current_round == Round.NA or table.get_pot() == 0:
            self.db.table_end_hand(table.id)
            return

        playing_seats = table.organised_seats.get_playing_seats()

        winning_seat = None
        if len(playing_seats) == 0:
            winning_seat = None
        elif len(playing_seats) == 1:
            winning_seat = playing_seats[0]
        else:
            winning_seat = self.determine_table_winner(table)

        if winning_seat:
            self.db.player_update_stack(table.id, winning_seat.player_id, table.pot)
            self.db.table_end_hand(table.id)
            self.db.table_reset_seats(table.id, table.get_seat_numbers())
            self.move_dealer_seat()

    def deal(self, table: Table):
        self.logger.debug("deal, table_id: {0}".format(table.id))

        if table.current_round == Round.PreFlop:
            self.deal_preflop(table)
        elif table.current_round == Round.Flop:
            self.deal_flop(table)
        elif table.current_round == Round.Turn:
            self.deal_turn(table)
        elif table.current_round == Round.River:
            self.deal_river(table)

    def deal_preflop(self, table: Table):
        self.logger.debug("deal_preflop, table_id: {0}, current_round: {1}".format(table.id, table.current_round))

        # Create a deck
        deck = self.create_deck()
        self.db.table_set_deck(table.id, deck)

        for seat in table.seats:
            seat_number = seat.seat_number

            # Give each player cards
            cards = self.deal_cards_from_deck(deck, 2)
            self.db.table_deal_hole_cards(table.id, seat_number, cards)

        # The dealer is the last player in the pre flop
        self.db.table_set_dealing_to_seat(table.id, table.dealer_seat_number)

    def deal_flop(self, table: Table):
        self.logger.debug("deal_flop, table_id: {0}".format(table.id))

        # Deal the board cards
        cards = self.deal_cards_from_deck(table.deck_cards, 3)
        self.db.table_deal_board_cards(table["_id"], cards)

        # The big blind is the last player in the turn
        big_blind_seat = table.get_big_blind()
        if big_blind_seat:
            self.db.table_set_dealing_to_seat(table.id, big_blind_seat.seat_number)

    def deal_turn(self, table):
        self.logger.debug("deal_turn, table_id: {0}".format(table.id))

        # Deal the board cards
        cards = self.deal_cards_from_deck(table.deck_cards, 1)
        self.db.table_deal_board_cards(table.id, cards)

        # The big blind is the last player in the turn
        big_blind_seat = table.get_big_blind()
        if big_blind_seat:
            self.db.table_set_dealing_to_seat(big_blind_seat.seat_number)

    def deal_river(self, table):
        self.logger.debug("deal_river, table_id: {0}".format(table.id))

        # Deal the board cards
        cards = self.deal_cards_from_deck(table.deck_cards, 3)
        self.db.table_deal_board_cards(table["_id"], cards)

        # The big blind is the last player in the turn
        big_blind_seat = table.get_big_blind()
        if big_blind_seat:
            self.db.table_set_dealing_to_seat(big_blind_seat.seat_number)

    def move_player_seat(self, table: Table):
        player_seat = table.get_dealer_seat()
        if player_seat is None:
            # If there is no player, the first seat should be the player
            player_seat = table.organised_seats.get_first_seat()
        else:
            # Otherwise get the next seat
            player_seat = table.organised_seats.get_next_seat(player_seat.seat_number)

        self.db.table_set_player_seat(table.id, player_seat.seat_number)

        table.turn_time_start = datetime.datetime.utcnow()
        self.db.table_set_turn_time_start(table.id, table.turn_time_start)

        return player_seat

    def move_dealer_seat(self, table: Table):
        dealer_seat = table.get_dealer_seat()
        if dealer_seat is None:
            # If there is no dealer, the first seat should be the dealer
            dealer_seat = table.organised_seats.get_first_seat()
        else:
            # Otherwise get the next seat
            dealer_seat = table.organised_seats.get_next_seat(dealer_seat.seat_number)

        self.db.table_set_dealer_seat(table.id, dealer_seat.seat_number)
        return dealer_seat

    def determine_table_winner(self, table: Table):
        seats = table.organised_seats.get_playing_seats()

        winning_seat = None
        winning_score = 0

        for seat in seats:
            hand_rank_str, score = HandRank.evaluate_hand(table.board_cards, seat.hole_cards)
            self.logger("hand_rank_str: {0}, score: {1}", hand_rank_str, score)

            if winning_seat is None or score > winning_score:
                winning_score = score
                winning_seat = seats

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