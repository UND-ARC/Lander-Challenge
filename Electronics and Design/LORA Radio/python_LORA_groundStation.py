import numpy as np
import adi
import time
import threading
import tkinter as tk
from ttkbootstrap import Style


class PlutoLoRaControl:
    def __init__(self, uri="usb:1.14.5"):
        # 1. Initialize Hardware
        try:
            self.sdr = adi.Pluto(uri)
            self.sdr.sample_rate = 1000000
            self.sdr.tx_rf_bandwidth = 2000000
            self.sdr.tx_lo = 915305000  # Match your Pi's 915.3MHz
            self.sdr.tx_hardwaregain_chan0 = -10  # -10 is strong, 0 is MAX

        except Exception as e:
            print(f"Hardware Error: Could not find Pluto at {uri}\n{e}")
            exit()

        # 2. State Management
        self.is_transmitting = False
        self.current_msg = ""

        # 3. GUI Setup
        self.root = tk.Tk()
        self.root.title("Lander-Challenge Ground Station")
        self.root.geometry("500x600")
        self.style = Style(theme="cyborg")

        # RSSI Label
        self.rssi_var = tk.StringVar(value="RSSI: -- dB")
        tk.Label(self.root, textvariable=self.rssi_var, font=("Helvetica", 12)).pack(pady=5)

        # UI Components
        tk.Label(self.root, text="PLUTO+ LORA COMMANDER", font=("Helvetica", 16)).pack(pady=20)

        # Start Button (Green)
        self.btn_start = tk.Button(self.root, text="HOLD TO STARTMAIN",
                                   bg="#28a745", fg="white", font=("Helvetica", 12, "bold"),
                                   height=3, width=25)
        self.btn_start.pack(pady=10)
        self.btn_start.bind("<ButtonPress-1>", lambda e: self.start_tx("STARTMAIN"))
        self.btn_start.bind("<ButtonRelease-1>", self.stop_tx)

        # ESTOP Button (Red)
        self.btn_stop = tk.Button(self.root, text="HOLD TO ESTOP",
                                  bg="#dc3545", fg="white", font=("Helvetica", 12, "bold"),
                                  height=3, width=25)
        self.btn_stop.pack(pady=10)
        self.btn_stop.bind("<ButtonPress-1>", lambda e: self.start_tx("ESTOP"))
        self.btn_stop.bind("<ButtonRelease-1>", self.stop_tx)

        # Log Terminal
        self.log = tk.Text(self.root, height=15, bg="#111", fg="#0f0")
        self.log.pack(pady=20, padx=20)

        self.write_log("System Ready. Connected to Pluto+.")
        threading.Thread(target=self.rssi_updater, daemon=True).start()
        self.root.mainloop()

    def get_rssi(self):
        try:
            # Some versions of the driver store it in the 'ad9361-phy' device
            # directly rather than the voltage channel
            return self.sdr._ctrl.debug_attrs['rssi'].value
        except:
            try:
                # Fallback to the voltage channel method
                return self.sdr._ctrl.find_channel('voltage0').attrs['rssi'].value
            except:
                return "-110.0"  # Default "silence" value

    def rssi_updater(self):
        while True:
            val = self.get_rssi()
            self.rssi_var.set(f"RSSI: {val}")
            time.sleep(0.5)

    def generate_lora_packet(self, message, sf=7, bw=125000, fs=1000000):
        """Mathematical LoRa Chirp Generator (Option B)"""
        N = int(fs * (2 ** sf / bw))
        t = np.arange(N) / fs

        # Preamble (8 raw up-chirps for Pi synchronization)
        preamble_chirp = np.exp(1j * np.pi * (bw / (2 ** sf / bw)) * (t ** 2))
        packet = [preamble_chirp] * 8

        # 2. SYNC WORD: This is where you "set" the word.
        # For a Private Network (0x12), we use 2.25 Down-chirps.
        down = np.exp(-1j * np.pi * (bw / (2 ** sf / bw)) * (t ** 2))
        packet.append(down)
        packet.append(down)
        packet.append(down[:int(N / 4)])  # The .25 trailing chirp

        # 3. MESSAGE: Standard LoRa shifted chirps
        # Add the RadioHead 4-byte header [To, From, ID, Flags]
        header = [chr(255), chr(255), chr(0), chr(0)]
        full_msg = "".join(header) + message

        for char in full_msg:
            val = ord(char) % (2 ** sf)
            shift_t = (np.arange(N) + (val * (N / 2 ** sf))) % N / fs
            shifted = np.exp(1j * np.pi * (bw / (2 ** sf / bw)) * (shift_t ** 2))
            packet.append(shifted)

        return (np.concatenate(packet) * 2047).astype(np.complex64)

    def start_tx(self, msg):
        self.is_transmitting = True
        self.current_msg = msg
        self.write_log(f"TX ACTIVE: Sending '{msg}' stream...")
        threading.Thread(target=self.tx_worker, daemon=True).start()

    def stop_tx(self, event):
        self.is_transmitting = False
        self.write_log("TX IDLE.")

    def tx_worker(self):
        """Background thread to push IQ samples without freezing the UI"""
        iq_data = self.generate_lora_packet(self.current_msg)
        while self.is_transmitting:
            try:
                self.sdr.tx(iq_data)
                time.sleep(0.02)  # Prevents USB buffer overflow
            except Exception as e:
                self.write_log(f"Hardware Error: {e}")
                break

    def write_log(self, text):
        timestamp = time.strftime("%H:%M:%S")
        self.log.insert(tk.END, f"[{timestamp}] {text}\n")
        self.log.see(tk.END)


if __name__ == "__main__":
    # Note: Double-check your URI with 'iio_info -s' if this fails
    PlutoLoRaControl()