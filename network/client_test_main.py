import time
from turtledemo.penrose import start

from Logger import Logger
from network.TemperatureSensor import TemperatureSensor
from network.client import NetworkClient

if __name__ == '__main__':
    logger = Logger("logger_config.json")
    logger.start()

    client = NetworkClient("client_config.yaml", logger=logger)
    client.connect()

    sensor = TemperatureSensor("Temp-1")
    print("Sensor odczyt: ",sensor.read_value())

    def handle_sensor_data(sensor_id, timestamp, value, unit):
        logger.log_reading(sensor_id,timestamp,value, unit)
        data = {
            "sensor_id": sensor_id,
            "timestamp": timestamp.isoformat(),
            "value": value,
            "unit": unit
        }
        success = client.send(data)
        if not success:
            print("Nie udało się wysłać danych")
    sensor.register_observer(handle_sensor_data)
    try:
        while True:
            sensor.read_value()
            time.sleep(sensor.frequency)
    except KeyboardInterrupt:
        print("⛔ Przerwano.")
    finally:
        client.close()
        logger.stop()