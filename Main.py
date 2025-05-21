import time
from Logger import Logger
from LightSensor import LightSensor
from TemperatureSensor import TemperatureSensor

if __name__ == "__main__":
        # Inicjalizacja loggera
        logger = Logger("logger_config.json")
        logger.start()

        # Tworzenie czujników
        light_sensor = LightSensor("light_1")
        temp_sensor = TemperatureSensor("temp_1", "Temperatura", "°C", -20, 40)

        # Rejestracja loggera jako obserwatora
        light_sensor.register_observer(logger.log_reading)
        temp_sensor.register_observer(logger.log_reading)

        try:
            while True:

                light_value = light_sensor.read_value()
                temp_value = temp_sensor.read_value()

                print(f"Światło: {light_value} {light_sensor.unit}")
                print(f"Temperatura: {temp_value} {temp_sensor.unit}")

                time.sleep(1)
        except KeyboardInterrupt:
            logger.stop()