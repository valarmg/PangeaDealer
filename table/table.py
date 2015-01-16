from random import randint
from pangeabetting import PangeaBetting
from pot import PangeaPot
from seat import PangeaSeat
from handhistory import HandHistory


class PangeaTable:

    def __init__(self, table_type="Holdem NoLimit", table_limits="1/2", table_size=2):
        self._type = table_type
        self._limits = table_limits
        self._numplayers = table_size
        self.name = self.__create_name()
        self.__blinds_specify(table_limits)
        self.seats_array = [None] * self._numplayers
        self._button = -1
        self.hh = HandHistory(table_type,table_limits,table_size)   #Creates a hh object for the table
        for i in range(0,self._numplayers):
            self.seats_array[i] = PangeaSeat(i)


    def __blinds_specify(self,table_limits):
        blinds_str = table_limits.split('/')
        self._big_blind = int(blinds_str[1])
        self._small_blind = int(blinds_str[0])


    def __create_name(self):
        id = randint(1000,9999)
        #Later: change this to choose from list of tables and get Lobby to keep track
        return "table" + str(id)

    def join_table(self, player_name, seat_num, stack, type=0):
        self.seats_array[seat_num-1].sit(player_name)
        self.seats_array[seat_num-1].add_money_to_stack(stack)
        self.seats_array[seat_num-1].type = type

    def leave_table(self,player):
        pass

    def seating_status(self):
        out_str = ""
        for i in range(0,self._numplayers):
            out_str = out_str + "Seat" + str(i+1) + ":"
            out_str = out_str + self.seats_array[i].name
            out_str = out_str + "(" + str(self.seats_array[i]._stack) + ")"
            out_str = out_str + "|"
        return out_str

    def inc_button(self):
        if (self._button == -1):
            self._button = randint(0,self._dealing_to-1)   # randomize button at start
        else:
            self._button = (self._button + 1) % self._dealing_to   #button points to dealing_order array

    def init_deal(self):
        #set up table for new deal
        self._dealing_order = []
        self._dealing_to = 0
        self.hh.init_summary_line()


        for i in range(0,self._numplayers):
            if (self.seats_array[i].is_in_play()):
                self._dealing_order.append(i)
                self._dealing_to += 1
        if (self._dealing_to > 1):
            self.inc_button()           #button doesn't work perfectly when someone gets knocked out under this logic

            self._dealing_order = self._dealing_order[self._button:] + self._dealing_order[:self._button]

            self._betting_order = list(self._dealing_order)
            return True
        else:
            return False

    def fold(self,player_no):
        self._dealing_order.remove(player_no)


if __name__ == "__main__":
    x = PangeaTable()
    print(x.name)