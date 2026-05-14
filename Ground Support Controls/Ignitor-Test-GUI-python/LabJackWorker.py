import math
import time
import csv
from datetime import datetime
from PyQt6 import QtCore
from labjack import ljm

class LabJackWorker(QtCore.QObject):
    # Signal to send the voltage to the UI
    # voltage_received = QtCore.pyqtSignal(float)
    labjack_signals = QtCore.pyqtSignal(dict)
    error_occurred = QtCore.pyqtSignal(str)

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



        self.channels_to_read = [
            "AIN0", #ox up
            "AIN1", #ch4 up
            "AIN2", #ox down
            "AIN3", #ch4 down
            "AIN4", #chamber
            "AIN48", # ox
            "AIN49", # ch4

        ]

        self.outputs = {
            "FIO0": 0.0,
            "FIO1": 0.0,
            "FIO2": 0.0,
            "FIO3": 0.0,
            "FIO4": 0.0,
            "FIO5": 0.0,
            "FIO6": 0.0,
            "FIO7": 0.0,
        }


        self.num_channels = len(self.channels_to_read)



    def run(self):
        try:
            #self.handle = ljm.openS("T7", "ETHERNET", "192.168.1.200")
            self.handle = ljm.openS("T7", "USB", "ANY")

            while self._running:
                # 1. Read from LabJack (This is the "blocking" part)
                # value = ljm.eReadName(handle, "AIN0")
                #value = 3.14  # Simulated reading
                results = ljm.eReadNames(self.handle, self.num_channels, self.channels_to_read)


                # TODO scale pressure values
                PT_00 = scale_value(results[0], 0, 5, 0, 1000)
                PT_01 = scale_value(results[1], 0, 5, 0, 1000)
                PT_02 = scale_value(results[2], 0, 5, 0, 1000)
                PT_03 = scale_value(results[3], 0, 5, 0, 1000)
                PT_04 = scale_value(results[4], 0, 5, 0, 870)

                TC_15 = scale_value(results[5], 0, 10, -150, 1370)
                TC_16 = scale_value(results[6], 0, 10, -150, 1370)

                output = {
                    "PT-00": PT_00,
                    "PT-01" : PT_01,
                    "PT-02" : PT_02,
                    "PT-03" : PT_03,
                    "PT-04" : PT_04,
                    "TC-15": TC_15,
                    "TC-16": TC_16,
                }

                GOXMassFlowRate, GOXFlowChoked = calculate_flow(output["PT-00"], output["PT-02"], output["TC-15"], "O2")

                CH4MassFlowRate, CH4FlowChoked = calculate_flow(output["PT-01"], output["PT-03"], output["TC-16"], "CH4")
                output["GOXMassFlowRate"] = GOXMassFlowRate
                output["GOXFlowChoked"] = GOXFlowChoked

                output["CH4MassFlowRate"] = CH4MassFlowRate
                output["CH4FlowChoked"] = CH4FlowChoked


                if self.loggingEnabled:
                    self.write_to_csv(list(output.values()))

                # 2. Emit the signals
                #self.voltage_received.emit(value)
                self.labjack_signals.emit(output)

                # 3. Frequency of reading (e.g., 10Hz = 0.1)
                time.sleep(0.004)
        except Exception as e:
            self.error_occurred.emit(str(e))
            raise e

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
            self.outputs[name] = value

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
                header = ["Timestamp"]
                header.extend(self.channels_to_read)
                header.extend(["GOXMassFlowRate", "GOXFlowChoked","CH4MassFlowRate", "CH4FlowChoked" ])
                header.extend(list(self.outputs.keys()))
                self.csv_writer.writerow(header)

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
            output = [timestamp] + data + list(self.outputs.values())
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


def calculate_flow(P1_psi, P2_psi, T1_C, gas_type='O2'):

    c_d = 0.8 #TODO confirm

    A = -1
    y = -1
    R = -1
    rho = -1

    T = T1_C + 273.15

    if gas_type == 'O2':
        y = 1.4
        A = 5.29*10**-7 # m^2
        R = 259.8 # kg / (m*s^2)
        rho = 1.429 # kg / m**3
    elif gas_type == 'CH4':
        y = 1.3
        A = 3.82*10*-7 # m^2
        R = 519.6 # kg / (m*s^2)
        rho = 0.717  # kg / m**3

    if P1_psi < P2_psi: #back flow
        return -1, False

    #source https://en.wikipedia.org/wiki/Choked_flow
    p_critical = P1_psi*(2/(y+1))**(y/(y-1))

    choked = P2_psi <= p_critical

    if choked:
        #for choked flow
        m_dot = c_d * A * P1_psi * math.sqrt(y/(R*T))*math.pow(2/(y+1),(y+1)/(2*(y-1)))

    else:
        m_dot = rho * c_d * A * math.sqrt((2 * (P1_psi-P2_psi))/rho)

    return m_dot, choked

