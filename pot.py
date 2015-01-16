from seat import PangeaSeat
from operator import itemgetter

class PangeaPot:

    _ROUND_PREFLOP = 0
    _ROUND_FLOP = 1
    _ROUND_TURN = 2
    _ROUND_RIVER = 3

    def __init__(self, big_blind, player_list):
        self._sidepots = []
        self._round_pot = 0
        self._total_pot = 0
        self._dead_money = 0
        self._uncontested_winner = -1
        self.round_bet = big_blind
        self._round = self._ROUND_PREFLOP
        self._bet_happened = False
        self._sidepots.append(sidepot())                            #sidepot[0]=mainpot


    def receive_bet(self,money):
        self._round_pot += money
        self._total_pot += money
        self._bet_happened = True

    def distribute_pots(self,table):
        no_of_sidepots = len(self._sidepots)
        for i in reversed(range(0,no_of_sidepots)):
            self._sidepots[i].distribute_pot(table, i, self._uncontested_winner)

    def increment_round_and_sort_pots(self,table):
        self._bet_happened = False
        self._round += 1
        self.sort_side_pots(table)
        self._round_pot = 0
        self.round_bet = 0
        self._dead_money = 0
        for i in table._dealing_order:
            table.seats_array[i].player_round_bet = 0


    def sort_side_pots(self, table):
        in_front_of_player_dict = {}
        for i in table._dealing_order:
            if table.seats_array[i].is_still_active():
                if table.seats_array[i].player_round_bet > 0:
                    in_front_of_player_dict[i] = table.seats_array[i].player_round_bet
        if len(in_front_of_player_dict) == 0:
            return                                  #everyone checked, no sidepots
        self.__srt_list_seats_array = sorted(in_front_of_player_dict.items(), key=itemgetter(1))
        #2-dim list, col=0 is the player seats, col=1 is the player_stacks
        self.rec_sort(0, table)


    def rec_sort(self, index, table):
        player_list = [self.__srt_list_seats_array[i][0] for i in range(index,len(self.__srt_list_seats_array)) ]
        self._sidepots[-1].seats_array_for_pot(player_list)
        if index == 0:
            amt = self.__srt_list_seats_array[index][1]                                #first pot of round,
        else:
            amt = self.__srt_list_seats_array[index][1] - self.__srt_list_seats_array[index-1][1]
        sidepot_amt = amt*len(player_list) + self._dead_money

        if (self.__srt_list_seats_array[index][1] == self.__srt_list_seats_array[-1][1]):       #if all seats_array put in same amount
            if (self.__srt_list_seats_array[index][0] == self.__srt_list_seats_array[-1][0]):   #if last one, thus uncalled bet
                table.hh.return_unmatched(table.seats_array[self.__srt_list_seats_array[index][0]],amt)
                table.seats_array[self.__srt_list_seats_array[index][0]].add_money_to_stack(amt)
                self._total_pot -= amt + self._dead_money
                self._sidepots[-1].add_to_pot(self._dead_money)
                return;
            self._sidepots[-1].add_to_pot(self._round_pot)
            if (self._round_pot != sidepot_amt):
                print("**********ERROR* mismatch in amount between ", str(self._round_pot), " and ", str(sidepot_amt))
            return

        self._sidepots[-1].add_to_pot(sidepot_amt)
        self._round_pot -= sidepot_amt
        for i in range(index,len(self.__srt_list_seats_array)):
            if (self.__srt_list_seats_array[index][1] != self.__srt_list_seats_array[i][1]):
                if i == len(self.__srt_list_seats_array) - 1:
                    pass
                self._sidepots.append(sidepot())
                self.rec_sort(i, table)
                break




class sidepot:

    def __init__(self):
        self.amount = 0
        self.players_in_pot = []

    def add_to_pot(self,amt):
        self.amount += amt

    def seats_array_for_pot(self,player_list):
        self.players_in_pot = player_list

    def compare_hands(self, table):
        min_score = 1000000
        win_seats_array = []
        for i in range(0,len(self.players_in_pot)):
            seat_i = table.seats_array[self.players_in_pot[i]]
            if seat_i.is_still_active():
                if not(seat_i.showed):
                    table.hh.player_show(table.seats_array[self.players_in_pot[i]])
                    seat_i.showed = True
                score = seat_i._rank_score
                rank = seat_i._rank_string
                if (score < min_score):
                    min_score = score
                    win_seats_array = [self.players_in_pot[i]]
                elif score == min_score:
                    win_seats_array.append(self.players_in_pot[i])
        if win_seats_array == []:
            print("************ERROR")
        return win_seats_array

    def distribute_pot(self,table, index, uncont_win):
        if uncont_win >= 0:
            seat_i = table.seats_array[uncont_win]
            seat_i.add_money_to_stack(self.amount)
            seat_i.amount_won += self.amount
            table.hh.player_won(seat_i,self.amount, index)
        else:
            winners = self.compare_hands(table)
            amt_for_player = self.amount/len(winners)
            for i in range(0,len(winners)):
                seat_i = table.seats_array[winners[i]]
                seat_i.add_money_to_stack(amt_for_player)
                table.hh.player_won(seat_i,amt_for_player, index)

                seat_i.amount_won += amt_for_player
                seat_i.showed = True

