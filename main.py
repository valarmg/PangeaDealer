from lobby.lobby import PangeaLobby
from table.table import PangeaTable
from player import PangeaPlayer
from deal.dealing import Deal
from deuces.card import Card

if __name__ == "__main__":
    Lobby = PangeaLobby()

    Table1 = Lobby.add_table("Holdem NoLimit", "1/2", 6)

    Player1 = PangeaPlayer("Kirk")
    Player1.add_money_to_stack(100)
    Player2 = PangeaPlayer("Spock")
    Player2.add_money_to_stack(100)
    Player3 = PangeaPlayer("KHAAANNNN!!!", 1)
    Player3.add_money_to_stack(100)

    Table1.join_table(Player1,1)
    Table1.join_table(Player2,2)
    Table1.join_table(Player3,3)


    x = Deal()
    x.shuffle()
    x.deal_hand(Table1)
