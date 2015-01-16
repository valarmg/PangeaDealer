from random import randint
import datetime
import sys
from pangeabetting import PangeaBetting
from pot import PangeaPot

class HandHistory:

    def __init__(self, table_type="Holdem NoLimit", table_limits="1/2", table_size=2):
        self.__type = table_type
        self.__limits = table_limits
        self.__numplayers = table_size          #table_size not used at the moment in hh
        self.__id = self.__create_hh_ID()
        #self.__file = open('handhistory.log', 'w')
        self.__file =  sys.stdout

    def __del__(self):
        self.__file.close()

    def __create_hh_ID(self):
        id = randint(100000,999900)
        return str(id)
        #This is temporary, will need a way to keep track of handhistories, so each new one gives a new number.

    def init_summary_line(self):
        line = "Pangea Poker Game #" + self.__id + ", " + self.__limits + " " + self.__type
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line += " - " + date + "\n"
        self.__file.write(line)

    def players_init_details(self, table):
        for i in range(0,table._numplayers):
            pl_details = "Seat " + str(i+1) + ": "
            if table.seats_array[i]:
                pl_details += table.seats_array[i].name
                if table.seats_array[i].name:
                    pl_details += " (" + str(table.seats_array[i]._stack) + ")"
                pl_details += "\n"
            self.__file.write(pl_details)

    def blinds_and_antes(self, table, big_blind, small_blind):
        if table._dealing_to == 2:
            sb_name = table.seats_array[table._dealing_order[1]].name
            bb_name = table.seats_array[table._dealing_order[0]].name
        else:
            sb_name = table.seats_array[table._dealing_order[0]].name
            bb_name = table.seats_array[table._dealing_order[1]].name

        blinds_details = sb_name + " posts small blind " + str(small_blind) + "\n"
        self.__file.write(blinds_details)
        blinds_details = bb_name + " posts big blind " + str(big_blind) + "\n"
        self.__file.write(blinds_details)

    def hole_cards_marker(self):
        line = "*** HOLE CARDS ***" + "\n"
        self.__file.write(line)

    def hole_cards(self,player):
        line = "Dealt to " + player.name + " [" + player.hole1 + " " + player.hole2 + "]" + "\n"
        self.__file.write(line)

    def flop(self, cards):
        line = "*** FLOP *** ["
        line += cards[0] +  " " + cards [1] + " " + cards[2] + "]" + "\n"
        self.__file.write(line)

    def turn(self, cards):
        line = "*** TURN *** ["
        line += cards[0] +  " " + cards [1] + " " + cards[2] + "] ["
        line += cards[3] + "]" + "\n"
        self.__file.write(line)

    def river(self, cards):
        line = "*** RIVER *** ["
        line += cards[0] +  " " + cards [1] + " " + cards[2] + "] ["
        line += cards[3] + "] ["
        line += cards[4] + "]" + "\n"
        self.__file.write(line)

    def showdown(self):
        line = "*** SHOW DOWN ***" + "\n"
        self.__file.write(line)

    def summary(self, pot, cards):
        line = "*** SUMMARY ***" + "\n"
        self.__file.write(line)
        line = "Total pot " + str(pot._total_pot) + "\n"
        self.__file.write(line)
        if len(cards) != 0:
            line= "Board ["
            if len(cards) > 0:
                line += cards[0] + " " + cards[1] + " " + cards[2]
            if len(cards) > 3:
                line += " " + cards[3]
            if len(cards) > 4:
                line += " " + cards[4]
            line += "]" + "\n"
            self.__file.write(line)

    def pl_summary(self, table, pot_amt):
        for i in range(0,table._numplayers):
            seat_i = table.seats_array[i]
            line = "Seat " + str(i+1) + ": "
            if seat_i.name != "":
                line += seat_i.name
                if seat_i._status == seat_i._SEAT_STATUS_SITTING_OUT:
                    line += " is sitting out"
                else:
                    if seat_i.position != "":
                         line += " (" + seat_i.position + ")"
                    if seat_i.is_still_active():
                        if seat_i._won_uncontested:
                            line += " collected (" + str(seat_i.amount_won) + ") "
                        else:
                            line += " showed [" + seat_i.hole1 + " " + seat_i.hole2 + "]"
                            if seat_i.amount_won == 0:
                                line += " and lost "
                            else:
                                line += " and won (" + str(seat_i.amount_won) + ") "
                            line += "with (" + seat_i._rank_string + ")"
                    else:
                        line += " folded "
                        if seat_i._status == seat_i._SEAT_STATUS_FOLDED_PREFLOP:
                            line += "before Flop"
                            if seat_i._didnt_bet:
                                line += " (didn't bet)"
                        elif seat_i._status == seat_i._SEAT_STATUS_FOLDED_FLOP:
                            line += "on the Flop"
                        elif seat_i._status == seat_i._SEAT_STATUS_FOLDED_TURN:
                            line += "on the Turn"
                        elif seat_i._status == seat_i._SEAT_STATUS_FOLDED_RIVER:
                            line += "on the River"

            line += "\n"
            self.__file.write(line)

    def player_positions_define(self, table):
        if (table._dealing_to == 2):
            table.seats_array[table._dealing_order[1]].position = "small blind"
            table.seats_array[table._dealing_order[0]].position = "big blind"
        else:
            table.seats_array[table._dealing_order[0]].position = "small blind"
            table.seats_array[table._dealing_order[1]].position = "big blind"
            table.seats_array[table._dealing_order[-1]].position = "button"

    def player_show(self, player):
        line = player.name + ": shows [" + player.hole1 + " " + player.hole2 + "] (" + player._rank_string + ")" + "\n"
        self.__file.write(line)

    def player_won(self, player, amount, index):
        line = player.name + ": collected " + str(amount) + " from "
        if (index == 0):
            pot_des = "main pot"
        else:
            pot_des = "side pot-" + str(index)
        line += pot_des
        line += "\n"
        self.__file.write(line)


    def return_unmatched(self, player, amount):
        line = "Uncalled bet (" + str(amount) + ") returned to " + player.name
        line += "\n"
        self.__file.write(line)

    def hole_cards(self,player):
        line = "Dealt to " + player.name + " [" + player.hole1 + " " + player.hole2 + "]" + "\n"
        self.__file.write(line)

    def player_bet(self,player, amount):
        line = player.name + ": bets " + str(amount)
        line = self.__is_allin(line,player)
        line += "\n"
        self.__file.write(line)

    def player_folds(self,player):
        line = player.name + ": folds" + "\n"
        self.__file.write(line)

    def player_checks(self,player):
        line = player.name + ": checks" + "\n"
        self.__file.write(line)

    def player_calls(self,player, amount):
        line = player.name + ": calls " + str(amount)
        line = self.__is_allin(line,player)
        line += "\n"
        self.__file.write(line)

    def player_raises(self,player, amount, total_raise):
        line = player.name + ":  raises " + str(amount) + " to " + str(total_raise)
        line = self.__is_allin(line,player)
        line += "\n"
        self.__file.write(line)

    def __is_allin(self, line, player):
        if (player._status == player._SEAT_STATUS_ALLIN):
            line += " and is all-in"
        return line