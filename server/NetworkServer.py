
import sys
import socket
import json
import threading
from datetime import datetime

import yaml

class NetworkServer:
    def __init__(self, port: int = None, config_path: str = "server_config.yaml"):
        """Inicjalizuje serwer na wskazanym porcie."""
        self.on_data_received = None
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
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                print(f"Połączono do {addr} [Server]")
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket,), daemon=True)
                client_thread.start()
        except KeyboardInterrupt:
            print(f"\n Zatrzymano server (ctrl + C) [Server]")
        finally:
            self.server_socket.close()

    def _deserialize(self, raw: bytes) -> dict:
        return json.loads(raw.decode("utf-8").strip())

    def register_callback(self, callback):
        self.on_data_received = callback

    def _handle_client(self, client_socket) -> None:
        try:
            buffer = b""
            while True:
                data_part = client_socket.recv(1024)
                if not data_part:
                    print("Klient się rozłączył. [Server]")
                    break
                buffer += data_part
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    try:
                        data = self._deserialize(line + b"\n")
                        print("Otrzymano dane: [Server]")
                        for k, v in data.items():
                            print(f"    {k}: {v}")

                        if self.on_data_received:
                            sensor_id = data["sensor_id"]
                            value = float(data["value"])
                            unit = data.get("unit", "")
                            timestamp = datetime.strptime(data["timestamp"], '%Y-%m-%dT%H:%M:%S.%f')
                            self.on_data_received(sensor_id, timestamp, value, unit)

                        ACK = json.dumps({"status": "ACK"}).encode("utf-8") + b"\n"
                        client_socket.sendall(ACK)
                        print("Wysłano ACK. [Server]")

                    except json.JSONDecodeError as ex:
                        print(f"[JSON Error]: {ex}")

        except Exception as ex:
            print(f"[BŁĄD klienta] {ex}", file=sys.stderr)
        finally:
            client_socket.close()
            print("Połączenie zamknięte. [Server]\n")