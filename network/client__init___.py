import random
import time
import sys
import signal
import atexit

from logger.Logger import Logger
from NetworkClient import NetworkClient
from sensors.AirQualitySensor import AirQualitySensor
from sensors.HumiditySensor import HumiditySensor
from sensors.LightSensor import LightSensor
from sensors.TemperatureSensor import TemperatureSensor

logger = Logger('logger_config.json')
logger.start()

client_config = "client_config.yaml"
client = NetworkClient(config_path=client_config, logger=logger)

sensors = [
    TemperatureSensor(sensor_id="Temp1"),
    HumiditySensor(sensor_id="Humid1"),
    AirQualitySensor(sensor_id="AirQual1"),
    LightSensor(sensor_id="Light1")
]

def handle_exit(signum, frame):  # przy nagłym wyjściu z programu, zapisz buffor loggera
    print("\n[EXIT] Zapisuję logi i zamykam połączenia...")
    logger.stop()
    client.close()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)  # Ctrl+C
signal.signal(signal.SIGTERM, handle_exit)  # kill

atexit.register(logger.stop)
atexit.register(client.close)

# rejestruje callbacki dla każdego sensora
for sensor in sensors:
    sensor.register_observer(logger.log_reading)
    sensor.register_observer(lambda sid, ts, val, unit: client.send({
        "sensor_id": sid,
        "timestamp": ts.isoformat(),
        "value": val,
        "unit": unit
    }))

try:
    client.connect()

    while True:
        chosen_sensor = random.choice(sensors)
        chosen_sensor.read_value()  #losowo wyślij dane jednego z sensorów
        time.sleep(2)

except Exception as e:
    print(f"[Client] Błąd: {e}")

finally:
    client.close()
    logger.stop()