from pot import pot
from player import PangeaPlayer


class betting:
    def __init__(self,blind):
        self.big_blind = blind
        self.small_blind = blind/2

    def player_bet(self,play1,pot1,money):
        if isinstance(money, float):
            if money.is_integer():
                money = int(money)
        pot1.receive_bet(money)
        play1.bet(money)
        play1.player_round_bet += money

    def post_blinds(self,table,pot1):
        #ensure this isn't called unless there are 2 players
        bet_to_player = 2
        if (table._dealing_to == 2):
            self.player_bet(table.players[table._dealing_order[0]],pot1,self.big_blind)
            self.player_bet(table.players[table._dealing_order[1]],pot1,self.small_blind)
        else:
            self.player_bet(table.players[table._dealing_order[0]],pot1,self.small_blind)
            self.player_bet(table.players[table._dealing_order[1]],pot1,self.big_blind)

    def betting_round(self, table,pot,bet_order):
        #every player must have a chance to bet, thereafter, betting will stop when everyone has put in same amount or are all-in
        j = 0
        one_rotation = False
        bet_happened = False
        while (True):
            i = bet_order[j]
            bet_to_player = pot.round_bet - table.players[i].player_round_bet
            bet_amount = table.players[i].player_bet_response(pot,bet_to_player)
            self.player_bet(table.players[i],pot,bet_amount)
            if bet_amount==0:
                if (bet_to_player == 0):
                    table.hh.player_checks(table.players[i])
                else:
                    table._dealing_order.remove(i)
                    table.hh.player_folds(table.players[i])
            elif bet_amount == bet_to_player:
                bet_happened == True
                table.hh.player_calls(table.players[i],bet_to_player)
            else:
                pot.round_bet += bet_amount - bet_to_player
                if (bet_happened):
                    table.hh.player_raises(table.players[i],bet_amount - bet_to_player,bet_amount)
                else:
                    table.hh.player_bet(table.players[i],bet_amount)
                bet_happened = True

            j += 1
            if j >= len(bet_order):
                one_rotation = True
                j = 0
            if (one_rotation and (table.players[bet_order[j]].player_round_bet==pot.round_bet)):
                break;








    def post_betting_round(self, table,pot):
        pass