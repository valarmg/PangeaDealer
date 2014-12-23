#This player is only playing at one table
class PangeaPlayer:

    def __init__(self, name, type=0):
        self.name = name
        self._stack = 0
        self.__type = type    #TEMP   for simple automatic response. type = 0 is calling player. type = 1 always raising pot player, type 2 =folding player
        self.player_round_bet = 0
        self.showdown_ranking = 0


    def add_money_to_stack(self,money):
        self._stack += money

    def bet(self,money):
        self._stack -=money

    def receive_hole_cards(self,card1,card2):
        self.hole1 = card1
        self.hole2 = card2


    def player_bet_response(self,cur_pot,bet_to):
        if (self.__type == 0):
            bet_amount = bet_to
        elif (self.__type == 1):
            bet_amount = int((cur_pot._pot + 2 * bet_to)*.5)    #This is 50% pot sized raise.
        elif (self.__type == 2):
            bet_amount = 0
        return bet_amount