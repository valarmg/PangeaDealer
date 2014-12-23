from random import randint
import datetime
from betting import betting
from pot import pot

#EAsy way to redirect output to file: http://stackoverflow.com/questions/4675728/redirect-stdout-to-a-file-in-python

class HandHistory:

    def __init__(self, table_type="Holdem NoLimit", table_limits="1/2", table_size=2):
        self.__type = table_type
        self.__limits = table_limits
        self.__numplayers = table_size          #table_size not used at the moment in hh
        self.__id = self.__create_hh_ID()

    def __create_hh_ID(self):
        id = randint(100000,999900)
        return str(id)
        #This is temporary, will need a way to keep track of handhistories, so each new one gives a new number.

    def summary_line(self):
        line = "Pangea Poker Game #" + self.__id + ", " + self.__limits + " " + self.__type
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line += " - " + date
        print(line)

    def players_init_details(self, table):
        for i in range(0,table._numplayers):
            pl_details = "Seat " + str(i+1) + ": "
            if table.players[i]:
                pl_details += table.players[i].name
                pl_details += " (" + str(table.players[i]._stack) + ")"
            print(pl_details)

    def blinds_and_antes(self, table, big_blind):
        sb = big_blind/2
        if sb.is_integer():
            sb = int(sb)
        blinds_details = table.players[table._dealing_order[0]].name + " posts small blind " + str(sb)
        print(blinds_details)
        blinds_details = table.players[table._dealing_order[1]].name + " posts big blind " + str(big_blind)
        print(blinds_details)

    def hole_cards_marker(self):
        line = "*** HOLE CARDS ***"
        print(line)

    def hole_cards(self,player):
        line = "Dealt to " + player.name + " [" + player.hole1 + " " + player.hole2 + "]"
        print(line)

    def flop(self, cards):
        line = "*** FLOP *** ["
        line += cards[0] +  " " + cards [1] + " " + cards[2] + "]"
        print(line)

    def turn(self, cards):
        line = "*** TURN *** ["
        line += cards[0] +  " " + cards [1] + " " + cards[2] + "] ["
        line += cards[3] + "]"
        print(line)

    def river(self, cards):
        line = "*** RIVER *** ["
        line += cards[0] +  " " + cards [1] + " " + cards[2] + "] ["
        line += cards[3] + "] ["
        line += cards[4] + "]"
        print(line)

    def showdown(self):
        line = "*** SHOW DOWN ***"
        print(line)

    def summary(self, pot, cards):
        line = "*** SUMMARY ***"
        print(line)
        line = "Total pot " + str(pot._pot)
        print(line)
        line= "Board ["
        line += cards[0] + " " + cards[1] + " " + cards[2] + " " + cards[3] + " " + cards[4] + "]"
        print(line)

    def pl_summary(self, table, pot_amt, winner):
        for i in range(0,table._numplayers):
            line = "Seat " + str(i+1) + ": "
            if table.players[i]:
                line += table.players[i].name
                line += " showed [" + table.players[i].hole1 + " " + table.players[i].hole2 + "]"
                if i==winner:
                    line += " and won (" + str(pot_amt) + ") "
                else:
                    line += " and lost "
                line += "with (" + table.players[i].showdown_ranking + ")"
            print(line)

    def player_show(self, player, result):
        line = player.name + ": shows [" + player.hole1 + " " + player.hole2 + "] (" + result + ")"
        print(line)

    def player_won(self, player, amount):
        line = player.name + ": collected " + str(amount) + " from pot"
        print(line)

    def hole_cards(self,player):
        line = "Dealt to " + player.name + " [" + player.hole1 + " " + player.hole2 + "]"
        print(line)

    def player_bet(self,player, amount):
        line = player.name + ": bets " + str(amount)
        print(line)

    def player_folds(self,player):
        line = player.name + ": folds"
        print(line)

    def player_checks(self,player):
        line = player.name + ": checks"
        print(line)

    def player_calls(self,player, amount):
        line = player.name + ": calls " + str(amount)
        print(line)

    def player_raises(self,player, amount, total_raise):
        line = player.name + ":  raises " + str(amount) + " to " + str(total_raise)
        print(line)