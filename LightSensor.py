from Sensor import Sensor
import datetime

class LightSensor(Sensor):
    def __init__(self, sensor_id, name = "Czujnik światła", unit = "lx", min_value = 0, max_value = 100000, frequency=1):
        super().__init__(sensor_id, name, unit, min_value, max_value, frequency)

    def get_light_value(self):
        """
            Zwraca zakres [min_value, max_value] w zależności od miesiąca i godziny.
            - W nocy jest ciemno, więc oswietlenie graniczy z 0.
            - Noc zaczyna się w różnych miesiącach o różnych godzinach.
        """
        now = datetime.datetime.now()
        month = now.month
        # hour = random.uniform(0,25)
        hour = now.hour

        zachody_wschody = {
            1: (8, 16),  # styczeń
            2: (7, 17),
            3: (6, 18),
            4: (5, 19),
            5: (4, 20),
            6: (4, 21),
            7: (4, 21),
            8: (5, 20),
            9: (6, 19),
            10: (6, 18),
            11: (7, 17),
            12: (8, 16)  # grudzień
        }
        wschod, zachod = zachody_wschody[month]
        if hour < wschod or hour >= zachod:
            self.max_value = 0
            self.min_value = 0
            return None
        monthly_max = {
            1: 20000, 2: 30000, 3: 40000, 4: 50000,
            5: 70000, 6: 100000, 7: 110000, 8: 100000,
            9: 80000, 10: 50000, 11: 30000, 12: 20000
        }
        by_month_max = monthly_max[month]
        self.min_value = 0
        self.max_value = by_month_max

    def read_value(self):
        """
           Użycie self.get_light_value() - dostosowanie zakresu.
           Wywołanie super().read_value() - ma na celu ograniczenie co ile czasu tworzone są nowe pomiary.
           (Jeżeli pomiary są tworzone mniej niż co sekundę, to wczytuje ostatnio zrobione pomiary.)
        """
        self.get_light_value()
        return super().read_value()