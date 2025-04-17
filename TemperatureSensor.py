import Sensor
import datetime
import random

class TemperatureSensor(Sensor):
    def __init__(self, sensor_id, name="Czujnik temperatury", unit="°C",min_value=-20, max_value=50, frequency=1):
        super().__init__(self, sensor_id, name, unit,min_value, max_value, frequency)

    def get_temperature_range(self):
        """
        Zwraca zakres temperatury zależny od aktualnego miesiąca.
        """
        month = datetime.datetime.now().month
        hour = datetime.datetime.now().hour

        temperature_ranges = {
            1: (-10, 5), 2: (-8, 7), 3: (-2, 12), 4: (5, 18),
            5: (10, 25), 6: (15, 30), 7: (18, 35), 8: (16, 33),
            9: (10, 25), 10: (5, 18), 11: (-2, 12), 12: (-8, 7)
        }
        min_temp, max_temp = temperature_ranges.get(month, (self.min_value, self.max_value))

        if 22 <= hour or hour < 6:
            temp_drop = random.randint(1, 5)
            min_temp = max(self.min_value, min_temp - temp_drop)
            max_temp = max(min_temp, max_temp - temp_drop)

        return min_temp, max_temp

    def read_value(self):
        """
        Generuje losową temperaturę zgodnie z aktualnym miesiącem i porą dnia.
        """
        if not self.active:
            raise Exception(f"{self.name} jest wyłączony.")

        min_value, max_value = self.get_temperature_range()
        value = random.uniform(min_value, max_value)
        self.last_value = round(value, 2)
        return self.last_value
