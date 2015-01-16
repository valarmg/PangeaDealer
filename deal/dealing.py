from random import shuffle as randshuff
from pot import PangeaPot
from pangeabetting import PangeaBetting


class PangeaDeal:

    def __init__(self):
        pass

    def shuffle(self):
        self.__dealt_cards = []
        self.__cards = list(range(0,51))
        randshuff(self.__cards)
        #Consider using a more random generator like SystemRandom
        #https://docs.python.org/2/library/random.html#random.SystemRandom
        #probably need to build the shuffle function by hand using it, if we do
        #I guess it'd be interesting to test distribution to check how it works

    def deal_card(self):
        cd1 =  self.convert_card_from_num(self.__cards.pop())
        self.__dealt_cards.append(cd1)
        return cd1

    def convert_card_from_num(self,card):
        conversion_suit = ("h","s","d","c")
        converstion_rank = ("A","2","3","4","5","6","7","8","9","T","J","Q","K")
        [suit,rank] = divmod(card,13)
        suit1 = conversion_suit[suit]
        rank1 = converstion_rank[rank]
        return rank1 + suit1

    def deal_hand(self, table):
        self.shuffle()
        Bet = PangeaBetting(table._big_blind,table._small_blind)
        for i in range(0,table._numplayers):
            table.seats_array[i].reset_details_for_new_hand()
        if table.init_deal():
            newP = PangeaPot(table._big_blind, table._dealing_order)

            table.hh.players_init_details(table)
            Bet.post_blinds(table,newP)
            table.hh.blinds_and_antes(table,table._big_blind,table._small_blind)

            table.hh.hole_cards_marker()
            for i in table._dealing_order:
                table.seats_array[i].receive_hole_cards(self.deal_card(),self.deal_card())
                table.hh.hole_cards(table.seats_array[i])

            table.hh.player_positions_define(table)

            self.deal_betting_section(table, Bet, newP)

            newP.distribute_pots(table)

            table.hh.summary(newP,self.board_cards)
            table.hh.pl_summary(table,newP._total_pot)
            return True
        else:
            print("Doesn't have two players, can't deal.")
            return False

    def deal_betting_section(self, table, Bet, newP):
        if table._dealing_to == 2:
            pre_bet_order = table._dealing_order[1:] + table._dealing_order[:1]
        else:
            pre_bet_order = table._dealing_order[2:] + table._dealing_order[:2]
        Bet.betting_round(table,newP,pre_bet_order)
        newP.increment_round_and_sort_pots(table)

        if self.is_there_uncontested_winner(table, newP):
            self.board_cards = []
            return

        self.board_cards = [self.deal_card(),self.deal_card(),self.deal_card()]
        table.hh.flop(self.board_cards)


        if len(table._betting_order) > 1:
            Bet.betting_round(table,newP,table._dealing_order)
            newP.increment_round_and_sort_pots(table)
        if self.is_there_uncontested_winner(table, newP):
            return

        self.board_cards += [self.deal_card()]
        table.hh.turn(self.board_cards)

        if len(table._betting_order) > 1:
            Bet.betting_round(table,newP,table._dealing_order)
            newP.increment_round_and_sort_pots(table)
        if self.is_there_uncontested_winner(table, newP):
            return

        self.board_cards += [self.deal_card()]
        table.hh.river(self.board_cards)

        if len(table._betting_order) > 1:
            Bet.betting_round(table,newP,table._dealing_order)
            newP.increment_round_and_sort_pots(table)
        if self.is_there_uncontested_winner(table, newP):
            return

        table.hh.showdown()

        for i in range(0, table._numplayers):
            if table.seats_array[i].is_still_active():
                table.seats_array[i].rank_hand(self.board_cards)


    def is_there_uncontested_winner(self, table, pot):
        players_left = 0
        for i in table._dealing_order:
            if table.seats_array[i].is_still_active():
                seat_winner_i = i
                players_left += 1
        if players_left == 1:
            pot._uncontested_winner = seat_winner_i
            table.seats_array[seat_winner_i]._won_uncontested = True
            return True
        else:
            return False



if __name__ == "__main__":
    x = PangeaDeal()
    x.shuffle()



