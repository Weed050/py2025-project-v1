import sys
import socket
import json
import yaml

class NetworkServer:
    def __init__(self, port: int = None, config_path: str = "server_config.yaml"):
        """Inicjalizuje serwer na wskazanym porcie."""
        if port is not None:
            self.port = port
        else:
            try:
                with open(config_path,"r",encoding="utf-8") as file:
                    config = yaml.safe_load(file)
                    self.port = config.get("port")
                    if not self.port:
                        raise ValueError("Brak wartości 'Port' w pliku konfiguracyjnym.")
            except Exception as ex:
                print(f"Błąd wczytywania konfiguracji: {ex}", file=sys.stderr)
                raise
        self.server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server_socket.bind(("0.0.0.0",self.port))
        self.server_socket.listen(5)
        print(f"Server nasłuchuje na porcie {self.port} ... [Server]")

    def start(self) -> None:
        """Uruchamia nasłuchiwanie połączeń i obsługę klientów."""
        try:
            while(True):
                client_socket, addr = self.server_socket.accept()
                print(f"Połączono do {addr} [Server]")
                self._handle_client(client_socket)
        except KeyboardInterrupt:
            print(f"\n Zatrzymano server (ctrl + C) [Server]")
        finally:
            self.server_socket.close()

    def _deserialize(self, raw: bytes) -> dict:
        return json.loads(raw.decode("utf-8").strip())

    def _handle_client(self, client_socket) -> None:
        """Odbiera dane, wysyła ACK i wypisuje je na konsolę."""
        try:
            buffer = b""
            while not buffer.endswith(b"\n"):
                part = client_socket.recv(1024)
                if not part:
                    break
                buffer += part
            try:
                data = self._deserialize(buffer)
                print("Otrzymano dane: [Server]")
                for k, v in data.items():
                    print(f"    {k}: {v}")
            except json.JSONDecodeError as ex:
                print(f"[JSON Error]: {ex}")
                client_socket.close()
                return

            ACK = json.dumps({"status":"ACK"}).encode("utf-8")+b"\n"
            client_socket.sendall(ACK)
            print("Wysłano ACK. [Server]")

        except Exception as ex:
            print(f"[BŁĄD klienta] {ex}", file=sys.stderr)
        finally:
            client_socket.close()
            print("Połączenie zamknięte. [Server]\n")