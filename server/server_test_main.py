from server import NetworkServer

# Inicjalizacja i start serwera (domyślnie z server_config.json)
server = NetworkServer(config_path="server_config.yaml")
server.start()