from table.table import PangeaTable

class PangeaLobby:
    __no_tables = 0
    __tables = None

    def __init__(self):
        pass

    def list_tables(self):
        return type(self).__no_tables

    def add_table(self, table_type="Holdem NoLimit", table_limits="1/2", table_size=2):
        type(self).__no_tables += 1
        y = PangeaTable(table_type, table_limits, table_size) #We'll start with default table
        return y
        #__tables.push(y)

    def remove_table(self, table_name=-1):
        type(self).__no_tables -= 1
        table_name = 1
        #__tables.remove(table_name)

if __name__ == "__main__":
    x= PangeaLobby()
    y = x.add_table()
    y.join_table()
    y.join_table()
    print(y.name)


