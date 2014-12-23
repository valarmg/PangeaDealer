from random import shuffle as randshuff
from pot import pot
from betting import betting
from deuces.card import Card
from deuces.evaluator import Evaluator

class Deal:

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
        newP = pot(2)     #hardcoding in BB for the moment
        Bet = betting(2)  #hardcoding in BB for the moment
        table.new_deal()
        table.hh.players_init_details(table)
        Bet.post_blinds(table,newP)
        table.hh.blinds_and_antes(table,newP.round_bet)

        table.hh.hole_cards_marker()
        for i in table._dealing_order:
            table.players[i].receive_hole_cards(self.deal_card(),self.deal_card())
            table.hh.hole_cards(table.players[i])

        pre_bet_order = table._dealing_order[2:] + table._dealing_order[:2]
        Bet.betting_round(table,newP,pre_bet_order)

        self.board_cards = [self.deal_card(),self.deal_card(),self.deal_card()]
        table.hh.flop(self.board_cards)
        Bet.betting_round(table,newP,table._dealing_order)

        self.board_cards += [self.deal_card()]
        table.hh.turn(self.board_cards)
        Bet.betting_round(table,newP,table._dealing_order)

        self.board_cards += [self.deal_card()]
        table.hh.river(self.board_cards)
        Bet.betting_round(table,newP,table._dealing_order)


        table.hh.showdown()

        rk = [None] * table._dealing_to
        sc = [None] * table._dealing_to
        for i in range(0,table._dealing_to): #this gets more complicated when people fold, and even more with side pots
            [rk[i],sc[i]] = self.evaluate_hand(self.board_cards,[table.players[i].hole1,table.players[i].hole2])
            table.hh.player_show(table.players[i],rk[i])
            table.players[i].showdown_ranking = rk[i]

        winner = self.compare_hands(sc)
        table.hh.player_won(table.players[winner],newP._pot)
        table.hh.summary(newP,self.board_cards)
        table.hh.pl_summary(table,newP._pot,winner)


        newP.distribute_pot(table.players[winner])

    def evaluate_hand(self,board,hand):
        dueces_board = [Card.new(board[0]),Card.new(board[1]),Card.new(board[2]),Card.new(board[3]),Card.new(board[4])]
        dueces_hand = [Card.new(hand[0]),Card.new(hand[1])]
        evaluator = Evaluator()
        score = evaluator.evaluate(dueces_board, dueces_hand)
        hand_rank = evaluator.get_rank_class(score)
        hand_rank_str = evaluator.class_to_string(hand_rank)
        return (hand_rank_str,score)

    def compare_hands(self,list_of_scores):
        return list_of_scores.index(min(list_of_scores))
        #We'll have to handle splits later


if __name__ == "__main__":
    x = Deal()
    x.shuffle()



