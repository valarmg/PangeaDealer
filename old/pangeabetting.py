class PangeaBetting:
    def __init__(self,blind,sm_blind):
        self.big_blind = blind
        self.small_blind = sm_blind

    def player_bet(self,pot1,money,table,seat):
        play1 = table.seats_array[seat]
        if play1.is_in_play():
            if (money > 0):
                if isinstance(money, float):
                    if money.is_integer():
                        money = int(money)
                if (money >= play1._stack):
                    money = play1._stack
                    play1.set_status_allin(table)

                pot1.receive_bet(money)
                play1.bet(money)
                play1.player_round_bet += money
            return money
        else:
            return -1

    def post_blinds(self,table,pot1):
        if (table._dealing_to == 2):
            self.player_bet(pot1,self.big_blind,table,table._dealing_order[0])
            self.player_bet(pot1,self.small_blind,table,table._dealing_order[1])
        else:
            self.player_bet(pot1,self.small_blind,table,table._dealing_order[0])
            self.player_bet(pot1,self.big_blind,table,table._dealing_order[1])

    def betting_round(self, table,pot,bet_order):
        #every player must have a chance to bet, thereafter, betting will stop when everyone has put in same amount or are all-in
        j = 0
        one_rotation = False
        while (True):
            i = bet_order[j]
            seat_i = table.seats_array[i]
            if seat_i.is_in_play():
                bet_to_player = pot.round_bet - seat_i.player_round_bet

                bet_amount = seat_i.player_bet_response(pot,bet_to_player)
                has_bet_happened = pot._bet_happened
                bet_amount = self.player_bet(pot,bet_amount,table,i)
                if bet_amount < 0:
                    pass
                elif bet_amount == 0:
                    if bet_to_player == 0:
                        table.hh.player_checks(seat_i)
                    else:
                        table.seats_array[i].set_status_folded(pot,table)
                        table.hh.player_folds(seat_i)
                        pot._dead_money += table.seats_array[i].player_round_bet
                elif bet_amount <= bet_to_player:
                    table.hh.player_calls(seat_i,bet_amount)
                else:
                    pot.round_bet += bet_amount - bet_to_player
                    if (has_bet_happened):
                        table.hh.player_raises(seat_i, bet_amount, seat_i.player_round_bet)
                    else:
                        table.hh.player_bet(seat_i, bet_amount)

            j += 1

            num_pls_left  = 0
            for i in table._dealing_order:
                if table.seats_array[i].is_in_play():
                    num_pls_left += 1
            if num_pls_left <= 1:
                break

            if j >= len(bet_order):
                one_rotation = True
                j = 0

            if (one_rotation and (table.seats_array[bet_order[j]].player_round_bet==pot.round_bet)):
                break;

