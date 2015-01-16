from lobby.lobby import PangeaLobby
from table.table import PangeaTable
from seat import PangeaSeat
from deal.dealing import PangeaDeal
from deuces.card import Card

def play_one_hand():
    Lobby = PangeaLobby()

    Table1 = Lobby.add_table("Holdem NoLimit", "1/2", 6)

    Table1.join_table("Kirk",1,12)
    Table1.join_table("Spock",2,17)
    Table1.join_table("KHAAANNNN!!!",3,100, 1)
    #Table1.join_table("Redshirt 1",6,100, 2)
    #Table1.join_table("Redshirt 2",4,100, 3)

    x = PangeaDeal()
    x.deal_hand(Table1)
    x.deal_hand(Table1)

def more_than_one_player_left(table):
    still_in_play = 0
    for i in range(0,table._numplayers):
        if (table.seats_array[i]._stack > 0):
            still_in_play += 1
    if (still_in_play >= 2):
        return True
    else:
        return False

def fixed_blinds_sit_n_go():
    Lobby = PangeaLobby()

    Table1 = Lobby.add_table("Holdem NoLimit", "1/2", 6)

    Table1.join_table("Kirk",1,12)
    Table1.join_table("Spock",2,17)
    Table1.join_table("KHAAANNNN!!!",3,100, 1)
    Table1.join_table("Redshirt 1",6,100, 2)
    Table1.join_table("Redshirt 2",4,40, 3)

    x = PangeaDeal()

    while(more_than_one_player_left(Table1)):
        if not(x.deal_hand(Table1)):
            break


if __name__ == "__main__":
    #play_one_hand()
    fixed_blinds_sit_n_go()




