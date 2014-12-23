from random import randint
from betting import betting
from pot import pot
from handhistory import HandHistory

class PangeaTable:

    def __init__(self, table_type="Holdem NoLimit", table_limits="1/2", table_size=2):
        self.__type = table_type
        self.__limits = table_limits
        self._numplayers = table_size
        self.name = self.__create_name()
        self.players = [None] * self._numplayers
        self._button = -1
        self.hh = HandHistory(table_type,table_limits,table_size)



    def __create_name(self):
        id = randint(1000,9999)
        #TODO: check if id is already used
        return "table" + str(id)

    def join_table(self,player,seat_num):
        self.players[seat_num-1] = player
        #If we are doing this async, have to worry about someone joining mid-deal

    def leave_table(self,player):
        pass

    def seating_status(self):
        out_str = ""
        for i in range(0,self._numplayers):
            out_str = out_str + "Seat" + str(i+1) + ":"
            if self.players[i]:
                out_str = out_str + self.players[i].name
                out_str = out_str + "(" + str(self.players[i]._stack) + ")"
            else:
                out_str = out_str + "Empty"
            out_str = out_str + "|"
        return out_str

    def inc_button(self):
        if (self._button == -1):
            self._button = randint(0,self._dealing_to-1)   # randomize button at start
        else:
            self._button = (self._button + 1) % self._dealing_to   #button points to dealing_order array

    def new_deal(self):
        #set up table for new deal
        self._dealing_order = []
        self._dealing_to = 0
        self.hh.summary_line()
        for i in range(0,self._numplayers):
            if self.players[i]:   #At the moment, everyone sitting is sitting in
                self._dealing_to += 1
                self.players[i].player_round_bet = 0

        self.inc_button()

        for i in range(0,self._numplayers):
            next_pl = (self._button + 1 + i) % self._numplayers
            if self.players[next_pl]:   #At the moment, everyone sitting is sitting in
                self._dealing_order.append(next_pl)

        self._dealing_to = len(self._dealing_order)

    def fold(self,player_no):
        self._dealing_order.remove(player_no)






if __name__ == "__main__":
    x = PangeaTable()
    print(x.name)
    #newP = pot()
    #x.new_deal()
    #x.post_blinds(newP)