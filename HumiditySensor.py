from Sensor import Sensor
import datetime

class HumiditySensor(Sensor):
    def __init__(self, sensor_id, name="Czujnik wilgotnosci", unit="%",min_value=0, max_value=100, frequency=1):
        super().__init__(sensor_id, name, unit,min_value, max_value, frequency)

    def read_value(self):
        now = datetime.datetime.now()
        hour = now.hour

        if 22 <= hour or hour < 6:
            humidity_range = (70, 100)
        elif 6 <= hour < 12:
            humidity_range = (50, 80)
        elif 12 <= hour < 18:
            humidity_range = (30, 60)
        else:
            humidity_range = (40, 70)

        self.min_value, self.max_value = humidity_range

        return super().read_value()
