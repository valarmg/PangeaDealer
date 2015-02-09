
class ClientManager(object):
    def __init__(self):
        self.clients = []

    def add_client(self, client):
        if client not in self.clients:
            self.clients.append(client)

    def remove_client(self, client):
        if client in self.clients:
            self.clients.remove(client)

    def get_clients(self):
        return self.clients

    def get_client_by_player_name(self, player_name):
        for client in self.clients:
            if client.player_name == player_name:
                return client
        return None

    def get_clients_by_table_id(self, table_id):
        for client in self.clients:
            if client.table_id == table_id:
                yield client