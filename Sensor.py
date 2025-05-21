
import random
import time
import datetime
from typing import List, Callable


class Sensor:
    def __init__(self, sensor_id, name, unit, min_value, max_value, frequency=1):
        """
        Inicjalizacja czujnika.

        :param sensor_id: Unikalny identyfikator czujnika
        :param name: Nazwa lub opis czujnika
        :param unit: Jednostka miary (np. '°C', '%', 'hPa', 'lux')
        :param min_value: Minimalna wartość odczytu
        :param max_value: Maksymalna wartość odczytu
        :param frequency: Częstotliwość odczytów (sekundy)
        """
        self.sensor_id = sensor_id
        self.name = name
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.frequency = frequency
        self.active = True
        self.last_value = None
        self.last_read_time = None
        self.observers: List[Callable[[str, datetime.datetime, float, str], None]] = []
        #               List[Callable[[sensor_ID, data, wartość, jednostka_miary], None <   - void]]

    def _notify_observers(self, value: float):
        timestamp = datetime.datetime.now()
        for callback in self.observers:
            try:
                callback(self.sensor_id, timestamp, value, self.unit)
            except Exception as e:
                print(f"Błąd w _notify_observers: {e}")

    def register_observer(self, callback : Callable[[str,datetime.datetime,float,str],None]):
        if callback in self.observers:
            self.observers.append(callback)

    def remove_observer(self, callback : Callable[[str,datetime.datetime,float,str],None]):
        if callback in self.observers:
            self.observers.remove(callback)

    def read_value(self):
        """
        Symuluje pobranie odczytu z czujnika.
        W klasie bazowej zwraca losową wartość z przedziału [min_value, max_value].
        Jeżeli zapytanie było wykonane mniej niż 1 sekundę temu, to zwróci ostatnio pobrany wynik.
        """
        if not self.active:
            raise Exception(f"{self.name} jest wyłączony.")

        current_time = time.time()

        if self.last_read_time is not None and current_time - self.last_read_time < 1:
            return self.get_last_value()

        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        value = round(random.uniform(self.min_value, self.max_value), 2)
        self.last_value = value
        self.last_read_time = current_time

        self._notify_observers(value)
        return value

    def calibrate(self, calibration_factor):
        """
        Kalibruje ostatni odczyt przez przemnożenie go przez calibration_factor.
        Jeśli nie wykonano jeszcze odczytu, wykonuje go najpierw.
        """
        if self.last_value is None:
            self.read_value()

        self.last_value *= calibration_factor
        return self.last_value

    def get_last_value(self):
        """
        Zwraca ostatnią wygenerowaną wartość, jeśli była wygenerowana.
        """
        if self.last_value is None:
            return self.read_value()
        return self.last_value

    def start(self):
        """
        Włącza czujnik.
        """
        self.active = True

    def stop(self):
        """
        Wyłącza czujnik.
        """
        self.active = False

    def __str__(self):
        return f"Sensor(id={self.sensor_id}, name={self.name}, unit={self.unit})"
