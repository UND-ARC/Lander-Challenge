import time
import csv
from datetime import datetime
from PyQt6 import QtCore
from labjack import ljm

class LabJackWorker(QtCore.QObject):
    # Signal to send the voltage to the UI
    #voltage_received = QtCore.pyqtSignal(float)
    labjack_signals = QtCore.pyqtSignal(dict)
    error_occurred = QtCore.pyqtSignal(str)

    #AIN 0-5 pressures, 12-13 temps
    channels_to_read = ["AIN0", "AIN1", "AIN2", "AIN3", "AIN4", "AIN5", "AIN6", "AIN12", "AIN13"]
    num_channels = len(channels_to_read)

    def __init__(self):
        super().__init__()
        self.handle = None
        self.loggingEnabled = False
        self._running = True
        self._output_queue = None  # To store pending writes
        self.filename = "temp.csv"
        self.log_file = None
        self.csv_writer = None
        self.flush_counter = 0



    def run(self):
        try:
            self.handle = ljm.openS("T7", "ANY", "ANY")

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
                pressure6 = results[6]

                #Temps
                temp12 = results[7]
                temp13 = results[8]

                # TODO scale pressure values
                PT_01 = scale_value(pressure0, 0, 24, 0, 24)
                PT_02 = scale_value(pressure1, 0, 24, 0, 24)
                PT_03 = scale_value(pressure2, 0, 24, 0, 24)
                PT_04 = scale_value(pressure3, 0, 24, 0, 24)
                PT_05 = scale_value(pressure4, 0, 24, 0, 24)
                PT_06 = scale_value(pressure5, 0, 24, 0, 24)
                PT_07 = scale_value(pressure6, 0, 24, 0, 24)

                CH4Temp = scale_value(temp12, 0, 10, -150, 1370)
                GOXTemp = scale_value(temp13, 0, 10, -150, 1370)




                output = {
                    "CH4Temp": CH4Temp,
                    "GOXTemp": GOXTemp,
                    "PT-01" : PT_01,
                    "PT-02" : PT_02,
                    "PT-03" : PT_03,
                    "PT-04" : PT_04,
                    "PT-05" : PT_05,
                    "PT-06" : PT_06,
                    "PT-07" : PT_07,
                }

                if self.loggingEnabled:
                    self.write_to_csv(list(output.values()))

                # 2. Emit the signals
                #self.voltage_received.emit(value)
                self.labjack_signals.emit(output)

                # 3. Frequency of reading (e.g., 10Hz = 0.1)
                time.sleep(0.004)
        except Exception as e:
            self.error_occurred.emit(str(e))

        finally:
            if self.handle:
                ljm.close(self.handle)
                # Ensure the file is closed even if the loop crashes
            if hasattr(self, 'log_file') and self.log_file:
                self.log_file.close()


    @QtCore.pyqtSlot(str, float)
    def write_value(self, name, value):
        """This method will be called by the GUI."""
        if self.handle is None:
            print("Can't write value, Labjack not connected")
            return

        try:
            # Direct write to the LabJack (e.g., setting a DAC or Digital Out)
            ljm.eWriteName(self.handle, name, value)
        except Exception as e:
            print(f"Write Error: {e}")

    def stop(self):
        self._running = False

    def setLoggingEnabled(self, enabled):
        if enabled and not self.loggingEnabled:
            # 1. Create a safe filename
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.filename = f'TestLog-{timestamp}.csv'

            try:
                # 2. Open the file once and keep it open
                self.log_file = open(self.filename, mode='w', newline='')
                self.csv_writer = csv.writer(self.log_file)

                # 3. Write headers
                self.csv_writer.writerow(["Timestamp", "CH4Temp", "GOXTemp", "PT-01", "PT-02", "PT-03", "PT-04", "PT-05", "PT-06", "PT-07"])

                # 4. Initialize flush counter
                self.flush_counter = 0
                self.loggingEnabled = True
                print(f"Logging started: {self.filename}")
            except Exception as e:
                self.error_occurred.emit(f"Failed to open log file: {e}")

        elif not enabled and self.loggingEnabled:
            # 5. Shut down logging safely
            self.loggingEnabled = False
            if hasattr(self, 'log_file') and self.log_file:
                try:
                    self.log_file.flush()
                    self.log_file.close()
                except Exception as e:
                    print(e)
                self.log_file = None
                print("Logging stopped and file saved.")


    def write_to_csv(self, data):
        if self.loggingEnabled and self.log_file:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            output = [timestamp] + data
            self.csv_writer.writerow(output)

            # --- FLUSH TIMER LOGIC ---
            # Increment counter. If 10Hz, 50 steps = 5 seconds.
            self.flush_counter += 1
            if self.flush_counter >= 50:
                self.log_file.flush()
                self.flush_counter = 0


def scale_value(voltage, min_in, max_in, min_out, max_out):
    # Prevent division by zero if the input range is invalid
    if max_in == min_in:
        return min_out

    # Calculate the scaled value
    scaled = min_out + ((voltage - min_in) * (max_out - min_out) / (max_in - min_in))

    return scaled

