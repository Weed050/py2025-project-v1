import os.path
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import yaml
from datetime import timedelta
from datetime import datetime

from numpy.ma.core import indices

from sensors.Sensor import Sensor
from sensors.TemperatureSensor import TemperatureSensor
from server.NetworkServer import NetworkServer
from logger.Logger import Logger


class SensorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Server GUI")

        # Konfiguracja
        self.load_config()
        self.server = None
        self.server_thread = None
        self.sensors = {}
        self.logger = Logger(os.path.join(os.path.dirname(__file__),"logger","logger_config.json"))
        self.logger.start()

        # UI
        self.setup_ui()

    def load_config(self):
        try:
            with open("server_config.yaml", "r") as f:
                self.config = yaml.safe_load(f)
        except:
            self.config = {"port": 12345}

    def save_config(self):
        with open("server_config.yaml", "w") as f:
            yaml.dump({"port": self.port_entry.get()}, f)

    def setup_ui(self):
        # Górny panel - sterowanie
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(control_frame, text="Port:").grid(row=0, column=0)
        self.port_entry = ttk.Entry(control_frame, width=10)
        self.port_entry.insert(0, str(self.config["port"]))
        self.port_entry.grid(row=0, column=1, padx=5)

        self.start_btn = ttk.Button(control_frame, text="Start", command=self.start_server)
        self.start_btn.grid(row=0, column=2, padx=5)

        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.stop_server, state="disabled")
        self.stop_btn.grid(row=0, column=3, padx=5)

        # Tabela czujników
        sensor_frame = ttk.Frame(self.root, padding="10")
        sensor_frame.grid(row=1, column=0, sticky="nsew")

        columns = ("Sensor", "Wartość", "Jednostka", "Timestamp", "Śr. 1h", "Śr. 12h")
        self.tree = ttk.Treeview(sensor_frame, columns=columns, show="headings", height=10)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")

        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(sensor_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pasek statusu
        self.status_var = tk.StringVar(value="Status: Zatrzymany")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken")
        status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        # Rozciąganie
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        sensor_frame.columnconfigure(0, weight=1)
        sensor_frame.rowconfigure(0, weight=1)

        # Aktualizacja interfejsu
        self.update_ui()


    def add_sensor(self, sensor):
        sensor.register_observer(self.handle_sensor_data)
        self.sensors[sensor.sensor_id] = {
            "obj": sensor,
            "values": [],
            "timestamps": []
        }

    def handle_sensor_data(self, sensor_id, timestamp, value, unit):
        if sensor_id not in self.sensors:
            new_sensor = Sensor(sensor_id=sensor_id, name=f"{sensor_id}", unit=unit)
            self.add_sensor(new_sensor)
        # logi danych
        self.logger.log_reading(sensor_id, timestamp, value, unit)

        # Aktualizacja danych czujnika
        if sensor_id in self.sensors:
            self.sensors[sensor_id]["values"].append(value)
            self.sensors[sensor_id]["timestamps"].append(timestamp)

            # Ogranicz historię do ostatnich 24h
            cutoff = datetime.now() - timedelta(hours=24)
            indices = [i for i, ts in enumerate(self.sensors[sensor_id]["timestamps"]) if ts >= cutoff]
            self.sensors[sensor_id]["values"] = [self.sensors[sensor_id]["values"][i] for i in indices]
            self.sensors[sensor_id]["timestamps"] = [self.sensors[sensor_id]["timestamps"][i] for i in indices]

            sensor = self.sensors[sensor_id]["obj"]
            sensor.last_value = value
            sensor.last_read_time = timestamp
            sensor.unit = unit
            self.root.after(0, self.update_ui)

    def calculate_average(self, sensor_id, hours):
        if sensor_id not in self.sensors or not self.sensors[sensor_id]["values"]:
            return 0.0

        cutoff = datetime.now() - timedelta(hours=24)
        values = [v for i, v in enumerate(self.sensors[sensor_id]["values"])
                  if self.sensors[sensor_id]["timestamps"][i] >= cutoff]

        return round(sum(values) / len(values), 2) if values else 0.0


    def start_server(self):
        try:
            port = int(self.port_entry.get())
            self.server = NetworkServer(port)

            self.server.register_callback(self.handle_sensor_data)

            # temp_sensor = Sensor(sensor_id="temp1", name="Temperatura", unit="°C", min_value=-20, max_value=50)
            # self.add_sensor(temp_sensor)

            # Uruchom serwer w osobnym wątku
            self.server_thread = threading.Thread(target=self.server.start, daemon=True)
            self.server_thread.start()

            self.status_var.set(f"Status: Nasłuchiwanie na porcie {port}")
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.save_config()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można uruchomić serwera: {str(e)}")

    def stop_server(self):
        if self.server:
            self.server.server_socket.close()
            self.server = None
            self.status_var.set("Status: Zatrzymany")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")

    def update_ui(self):
        MAX_RECORDS = 100

        # Czyścimy tabelę
        for item in self.tree.get_children():
            self.tree.delete(item)

        for sensor_id, data in self.sensors.items():
            sensor = data["obj"]
            values = data["values"]
            timestamps = data["timestamps"]
            unit = sensor.unit if sensor.unit else ""

            avg_1h = self.calculate_average(sensor_id, 1)
            avg_12h = self.calculate_average(sensor_id, 12)

            # Wstawiamy wiersz ze średnimi
            self.tree.insert("", "end", values=(
                f"{sensor.name} (Średnia)",
                "", "", "",
                avg_1h,
                avg_12h
            ))

            # Ostatnie rekordy
            recent_values = values[-MAX_RECORDS:]
            recent_timestamps = timestamps[-MAX_RECORDS:]

            for value, ts in zip(recent_values, recent_timestamps):
                time_str = ts.strftime("%Y-%m-%d %H:%M:%S") if ts else "-"
                self.tree.insert("", "end", values=(
                    sensor.name,
                    value,
                    unit,
                    time_str,
                    "",
                    ""
                ))

        # Zaplanuj ponowne odświeżenie
        self.root.after(5000, self.update_ui)

    def run(self):
        self.root.mainloop()
        if self.logger:
            self.logger.stop()


if __name__ == "__main__":
    root = tk.Tk()
    app = SensorGUI(root)
    app.run()