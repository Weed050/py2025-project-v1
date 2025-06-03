import json
import os.path
import socket
from datetime import datetime

import yaml

from logger.Logger import Logger

class NetworkClient:
    def __init__(
        self,
        config_path:str = None,
        host: str = None,
        port: int = None,
        timeout: float = 5.0,
        retries: int = 3,
        logger: Logger = None,
    ):
        """Inicjalizuje klienta sieciowego."""
        self.logger = logger

        if config_path:
            self._load_config(config_path)
        else:
            self.host = host
            self.port = port
            self.timeout = timeout
            self.retries = retries

    def _load_config(self, path:str)->None:

        """Przypisanie ustawień konfiguracji połączenia z pliku konfiguracyjnego."""

        if not os.path.exists(path) or os.path.getsize(path) == 0:
            raise FileNotFoundError(f"Plik {path} nie istnieje lub jest pusty")

        with open(path, 'r') as file:
            config = yaml.safe_load(file)

        keys = ["host", "port", "timeout", "retries"]
        missing = [k for k in keys if k not in config]
        if missing:
            raise ValueError(f"Brakuje wartości: {', '.join(missing)}")

        self.host = config["host"]
        self.port = config["port"]
        self.timeout = config["timeout"]
        self.retries = config["retries"]

    def connect(self) -> None:
        """Nawiazuje połączenie z serwerem."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            self._log_event("Połączono z serwerem", value=1.0)
        except Exception as ex:
            self._log_event("Połączono z serwerem", value=0.0, unit="error")
            raise

    def send(self, data: dict) -> bool:
        """Wysyła dane i czeka na potwierdzenie zwrotne."""
        serialized = self._serialize(data)

        for attempt in range(1,self.retries+1):
            try:
                self._log_event(f"Próba wysyłki (podejscie nr. {attempt})",value=1.0)
                self.socket.sendall(serialized)

                buffer = b""
                while not buffer.endswith(b"\n"):
                    part = self.socket.recv(1024)
                    if not part:
                        break
                    buffer += part
                ack_data = self._deserialize(buffer)
                if ack_data.get("status") == "ACK":
                    self._log_event("Otrzymano ACK", value=1.0)
                    return True
                else:
                    self._log_event(f"Nie prawidłowa odpowiedź: {ack_data}", value=0.0,unit="error")
            except socket.timeout:
                self._log_event(f"Brak odpowiedzi - timeout", value=0.0, unit="error")
            except Exception as ex:
                self._log_event(f"Błąd: {ex}", value=0.0, unit="error")

        self._log_event("Nie udało się wysłać po wszystkich próbach.",value=0.0, unit="error")
        return False



    def close(self) -> None:
        """Zamyka połączenie."""
        try:
            if self.socket:
                self.socket.close()
                self.socket = None
            self._log_event("Zamknięto połączenie", value=1.0)
        except Exception as ex:
            self._log_event(f"Wystąpił błąd podczas zamykania połączenia: {ex}", value=0.0, unit="error")

    # Metody pomocnicze:
    def _serialize(self, data: dict) -> bytes:
        return (json.dumps(data) + "\n").encode("utf-8")

    def _deserialize(self, raw: bytes) -> dict:
        return json.loads(raw.decode("utf-8").strip())

    # 1.0 - pass, 0.0 - error
    def _log_event(self,message: str, value: float = 1.0, unit: str = "Info")-> None:
        if self.logger:
            self.logger.log_reading( sensor_id="network_client",
                                     timestamp=datetime.now(),
                                     value= value,
                                     unit= message if unit == "Info" else f"ERROR: {message}"
                                     )