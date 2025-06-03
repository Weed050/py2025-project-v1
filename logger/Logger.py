import csv
import zipfile
from datetime import datetime
import json
import os
from typing import List, Iterator, Dict, Optional

class Logger:
    def __init__(self, config_path: str):
        with open(config_path,"r",encoding='utf-8') as file:
            data = json.load(file)
            self.log_dir = data["log_dir"]
            self.filename_pattern = data["filename_pattern"]
            self.buffer_size = data["buffer_size"]
            self.rotate_every_hours = data["rotate_every_hours"]
            self.max_size_mb = data["max_size_mb"]
            self.rotate_after_lines = data["rotate_after_lines"]
            self.retention_days = data["retention_days"]
            self.buffor : List[List[str]] = []
            self.last_rotation_time = datetime.now()
            self.fileName = None
            self.filePath = None
            self.stopped = False

        newpath = [self.log_dir,os.path.join(self.log_dir,"archive")]
        for i in newpath:
            if not os.path.exists(i):
                os.makedirs(i)
        """
        Inicjalizuje logger na podstawie pliku JSON.
        :param config_path: Ścieżka do pliku konfiguracyjnego (.json)
        """


    def start(self) -> None:
        """
        Otwiera nowy plik CSV do logowania. Jeśli plik jest nowy, zapisuje nagłówek.
        """
        flag_new_file = False
        time = datetime.now()
        self.fileName = time.strftime(self.filename_pattern)
        self.filePath = os.path.join(self.log_dir,self.fileName)


        if not os.path.isfile(self.filePath):
            flag_new_file = True
            self.last_rotation_time = datetime.now()

        self.csv_write = open(self.filePath,'a',newline='',encoding='utf-8')
        writer = csv.writer(self.csv_write)


        if flag_new_file:
            writer.writerow(["sensor_id","timestamp","value","unit"])

    def stop(self) -> None:
        """
        Wymusza zapis bufora i zamyka bieżący plik.
        """
        if self.stopped:
            return
        self.stopped = True
        if self.csv_write:
            if self.buffor:
                writer = csv.writer(self.csv_write)
                writer.writerows(self.buffor)
                self.buffor = []
            self.csv_write.flush()
            self.csv_write.close()
            self.csv_write = None

    def log_reading(
        self,
        sensor_id: str,
        timestamp: datetime,
        value: float,
        unit: str
    ) -> None:
        """
        Dodaje wpis do bufora i ewentualnie wykonuje rotację pliku.
        """
        row = [sensor_id,timestamp.isoformat(),value,unit]
        self.buffor.append(row)
        if len(self.buffor) >= self.buffer_size:
            writer = csv.writer(self.csv_write)
            writer.writerows(self.buffor)
            self.buffor = []

        # last rotation time
        diffHours = None
        if self.last_rotation_time:
            diffHours = (datetime.now()-self.last_rotation_time).total_seconds() / 3600
        else:
            self.last_rotation_time = datetime.now()

        if diffHours >= self.rotate_every_hours  or (self.max_size_mb * 1048576) <= os.path.getsize(self.filePath):
            filename, extension = os.path.splitext(self.filePath)
            if extension == ".csv":
                self._rotate()


    def _rotate(self):
        self.stop()

        archive_name = os.path.join(self.log_dir, "archive", self.fileName.replace(".csv", ".zip"))

        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(self.filePath, arcname=self.fileName)

        os.remove(self.filePath)

        self._clean_old_archives()

        self.start()

    def _clean_old_archives(self):
        archiveDir = os.path.join(self.log_dir, "archive")
        for file in os.listdir(archiveDir):
            filePath = os.path.join(archiveDir, file)
            fileAgeDays = (datetime.now() - datetime.fromtimestamp(os.path.getctime(filePath))).days
            if fileAgeDays >= self.retention_days:
                os.remove(filePath)

    def read_logs(
        self,
        start: datetime,
        end: datetime,
        sensor_id: Optional[str] = None
    ) -> Iterator[Dict]:
        """
        Pobiera wpisy z logów zadanego zakresu i opcjonalnie konkretnego czujnika.
        """
        # zwykłe logi
        for file in os.listdir(self.log_dir):
            filePath = os.path.join(self.log_dir,file)
            if file.endswith(".csv") and os.path.isfile(filePath):
                yield from self._readCsv(filePath,start,end,sensor_id)

        # logi z archiwum
        archiveDir = os.path.join(self.log_dir,"archive")
        for file in os.listdir(archiveDir):
            if file.endswith(".zip"):
                zipPath = os.path.join(archiveDir,file)
                with zipfile.ZipFile(zipPath,"r") as zipFle:
                    for name in zipFle.namelist():
                        if name.endswith(".csv"):
                            with zipFle.open(name) as csvF:
                                yield from self._readCsv(csvF,start, end, sensor_id)


    def _readCsv(self, filePath, start: datetime, stop: datetime,sensor_id : Optional[str]) -> Iterator[Dict]:
        with open(filePath,'r',encoding="utf-8") as fileCsv:
            reader = csv.DictReader(fileCsv)
            for row in reader:
                try:
                    timeSt = datetime.fromisoformat(row["timestamp"])
                    if start < timeSt <= stop:
                        if sensor_id is None or row["sensor_id"] == sensor_id:
                            yield {
                                  "timestamp": timeSt,
                                  "sensor_id": row["sensor_id"],
                                  "value": float(row["value"]),
                                  "unit": row["unit"]
                            }
                except Exception:
                    continue # pomija bledne wiersze