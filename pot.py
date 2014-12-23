from player import PangeaPlayer

class pot:


    def __init__(self, big_blind):
        self._pot = 0
        self.round_bet = big_blind

    def receive_bet(self,money):
        self._pot += money

    def distribute_pot(self,player):
        player.add_money_to_stack(self._pot)
        self._pot = 0
        #ignoring sidepots and splitpots for now