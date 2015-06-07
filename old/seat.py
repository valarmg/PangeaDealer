from utils import HandRank

#This player is only playing at one table
class PangeaSeat:
    _SEAT_STATUS_UNOCCUPIED = -2
    _SEAT_STATUS_SITTING_OUT = -1
    _SEAT_STATUS_INPLAY = 0
    _SEAT_STATUS_ALLIN = 1
    _SEAT_STATUS_FOLDED_PREFLOP = 10
    _SEAT_STATUS_FOLDED_FLOP = 11
    _SEAT_STATUS_FOLDED_TURN = 12
    _SEAT_STATUS_FOLDED_RIVER = 13

    def __init__(self, seat_index):
        self._stack = 0
        self.type = 0    #TEMP   for simple automatic response. type = 0 is calling player. type = 1 always raising pot player, type 2 =folding player
        self._status = self._SEAT_STATUS_UNOCCUPIED
        #self._rank_string = ""
        #self._rank_score = -1
        self.name = ""
        self._seatindex = seat_index

    def reset_details_for_new_hand(self):
        self.player_round_bet = 0
        self._rank_string = ""
        self._rank_score = -1
        self.amount_won = 0
        self.showed = False
        self.position = ""
        self._didnt_bet = True
        self._won_uncontested = False
        if (self._status >= 0):
            if (self._stack == 0):
                self._status = self._SEAT_STATUS_SITTING_OUT
            else:
                self._status = self._SEAT_STATUS_INPLAY


    def sit(self, name, stack=0):
        self.name = name
        self._stack = stack
        if self._stack == 0:
             self._status = self._SEAT_STATUS_SITTING_OUT
        else:
             self._status = self._SEAT_STATUS_INPLAY

    def set_status_allin(self, table):
        self._status = self._SEAT_STATUS_ALLIN
        table._betting_order.remove(self._seatindex)

    def is_in_play(self):
        if (self._status == self._SEAT_STATUS_INPLAY):
            return True
        else:
            return False

    def is_still_active(self):
        if (self._status == self._SEAT_STATUS_INPLAY) or (self._status == self._SEAT_STATUS_ALLIN):
            return True
        else:
            return False

    def set_status_folded(self, pot,table):
        if (pot._round == pot._ROUND_PREFLOP):
            self._status = self._SEAT_STATUS_FOLDED_PREFLOP
        elif (pot._round == pot._ROUND_FLOP):
            self._status = self._SEAT_STATUS_FOLDED_FLOP
        elif (pot._round == pot._ROUND_TURN):
            self._status = self._SEAT_STATUS_FOLDED_TURN
        elif (pot._round == pot._ROUND_RIVER):
            self._status = self._SEAT_STATUS_FOLDED_RIVER
        table._betting_order.remove(self._seatindex)

    def add_money_to_stack(self,money):
        self._stack += money
        self._status = self._SEAT_STATUS_INPLAY

    def bet(self,money):
        self._didnt_bet = False
        self._stack -=money

    def receive_hole_cards(self,card1,card2):
        self.hole1 = card1
        self.hole2 = card2

    def rank_hand(self,board_cards):
        if (self._status == self._SEAT_STATUS_INPLAY or self._status == self._SEAT_STATUS_ALLIN):
            eval = HandRank()
            [self._rank_string,self._rank_score] = eval.evaluate_hand(board_cards,[self.hole1,self.hole2])

    def player_bet_response(self,cur_pot,bet_to):
        if (self.type == 0):
            bet_amount = bet_to
        elif (self.type == 1):
            if (cur_pot._round == cur_pot._ROUND_PREFLOP):
                bet_amount = int((cur_pot._total_pot + 2 * bet_to))    #This is a pot sized raise.
            else:
                bet_amount = int((cur_pot._total_pot + 2 * bet_to)*.5)    #This is a 50% pot sized raise.
        elif (self.type == 2):
            if (cur_pot._round == cur_pot._ROUND_PREFLOP) or (cur_pot._round == cur_pot._ROUND_FLOP):
                bet_amount = bet_to
            else:
                bet_amount = 0
        elif (self.type == 3):
            bet_amount  = 0



        return bet_amount

