import time
import csv
from datetime import datetime
from PyQt6 import QtCore
from labjack import ljm

class LabJackWorker(QtCore.QObject):
    # Signal to send the voltage to the UI
    #voltage_received = QtCore.pyqtSignal(float)
    CH4Temp_signal = QtCore.pyqtSignal(float)
    GOXTemp_signal = QtCore.pyqtSignal(float)
    error_occurred = QtCore.pyqtSignal(str)

    #AIN 0-5 pressures, 12-13 temps
    channels_to_read = ["AIN0", "AIN1", "AIN2", "AIN3", "AIN4", "AIN5", "AIN12", "AIN13"]
    num_channels = len(channels_to_read)

    def __init__(self, handle):
        super().__init__()
        self.handle = handle
        self.loggingEnabled = False
        self._running = True
        self._output_queue = None  # To store pending writes
        self.filename = "temp.csv"

    def run(self):
        try:

            while self._running:
                # 1. Read from LabJack (This is the "blocking" part)
                # value = ljm.eReadName(handle, "AIN0")
                #value = 3.14  # Simulated reading
                results = ljm.eReadNames(self.handle, self.num_channels, self.channels_to_read)

                #pressures
                pressure0 = results[0]
                pressure1 = results[1]
                pressure2 = results[2]
                pressure3 = results[3]
                pressure4 = results[4]
                pressure5 = results[5]

                #Temps
                temp12 = results[6]
                temp13 = results[7]

                CH4Temp = scale_value(temp12, 0, 10, -150, 1370)
                GOXTemp = scale_value(temp13, 0, 10, -150, 1370)

                if self.loggingEnabled:
                    self.write_to_csv((CH4Temp, GOXTemp))

                # 2. Emit the signals
                #self.voltage_received.emit(value)
                self.CH4Temp_signal.emit(CH4Temp)
                self.GOXTemp_signal.emit(GOXTemp)

                # 3. Frequency of reading (e.g., 10Hz = 0.1)
                time.sleep(0.1)
        except Exception as e:
            self.error_occurred.emit(str(e))

    @QtCore.pyqtSlot(str, float)
    def write_value(self, name, value):
        """This method will be called by the GUI."""
        try:
            # Direct write to the LabJack (e.g., setting a DAC or Digital Out)
            ljm.eWriteName(self.handle, name, value)
        except Exception as e:
            print(f"Write Error: {e}")

    def stop(self):
        self._running = False

    def setLoggingEnabled(self, enabled):
        if not self.loggingEnabled and enabled:
            self.loggingEnabled = True
            self.filename = f'TestLog-{datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")}.csv'
            self.write_to_csv(("CH4Temp", "GOXTemp")) #headers


    def write_to_csv(self, data):
        # Open in 'append' mode so we don't overwrite previous data
        with open(self.filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            # Create a timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            # Write: Timestamp, AIN0, AIN1
            writer.writerow([timestamp] + list(data))


def scale_value(voltage, min_in, max_in, min_out, max_out):
    # Prevent division by zero if the input range is invalid
    if max_in == min_in:
        return min_out

    # Calculate the scaled value
    scaled = min_out + ((voltage - min_in) * (max_out - min_out) / (max_in - min_in))

    return scaled

