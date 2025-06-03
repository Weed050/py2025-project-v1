
import datetime
import random

from sensors.Sensor import Sensor


class AirQualitySensor(Sensor):
    def __init__(self, sensor_id, name="Czujnik jakości powietrza", unit="AQI", min_value=0, max_value=500, frequency=1):
        super().__init__(sensor_id, name, unit, min_value, max_value, frequency)

    def read_value(self):
        now = datetime.datetime.now()
        hour = now.hour

        # 0-50 - ok
        # 50-100 - średnie
        # 100-150 - niezdrowe dla grup ludzi wrażliwych
        # 150-200 - niezdrowe
        """
                Jakość powietrza jest zależna od godziny w ciągu dnia.
        """

        if 6 <= hour < 9:
            aqi_range = (80, 150)
        elif 9 <= hour < 16:
            aqi_range = (50, 120)
        elif 16 <= hour < 20:
            aqi_range = (100, 200)
        elif 20 <= hour < 23:
            aqi_range = (50, 100)
        else:
            aqi_range = (10, 60)

        if random.random() < 0.05:  # 5% szansy
            aqi_range = (200, 400)

        elif random.random() < 0.03:  # 3% szansy
            aqi_range = (0, 30)

        self.min_value, self.max_value = aqi_range
        return super().read_value()
