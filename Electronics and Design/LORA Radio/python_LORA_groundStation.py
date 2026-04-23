import sys
import time
import threading
import numpy as np
import adi
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton,
                             QVBoxLayout, QTextEdit, QLabel, QWidget)
from PyQt6.QtCore import QThread, pyqtSignal, Qt


class SDRWorker(QThread):
    """Handles the heavy lifting of SDR TX/RX in the background"""
    rssi_update = pyqtSignal(str)
    log_update = pyqtSignal(str)

    def __init__(self, uri="usb:1.9.5"):
        super().__init__()
        try:
            self.sdr = adi.Pluto(uri)
            self.sdr.sample_rate = 1000000
            self.sdr.tx_lo = 915000000
            self.sdr.tx_hardwaregain_chan0 = -10
            self.active = True
        except Exception as e:
            self.active = False
            print(f"SDR Init Failed: {e}")

    def run(self):
        """Monitor RSSI while the app is open"""
        while self.active:
            try:
                # Direct register read for AD9361 RSSI
                val = self.sdr._ctrl.find_channel('voltage0').attrs['rssi'].value
                self.rssi_update.emit(f"RSSI: {val} dB")
            except:
                pass
            time.sleep(0.5)


class GroundStation(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lander-Challenge Mission Control")
        self.setMinimumSize(500, 600)

        # 1. Logic State
        self.is_transmitting = False
        self.worker = SDRWorker()
        self.worker.rssi_update.connect(self.update_rssi)
        self.worker.start()

        # 2. UI Layout
        layout = QVBoxLayout()

        self.rssi_label = QLabel("RSSI: -- dB")
        self.rssi_label.setStyleSheet("font-size: 18px; color: #00ff00;")
        layout.addWidget(self.rssi_label)

        self.btn_start = QPushButton("HOLD TO STARTMAIN")
        self.btn_start.setStyleSheet("background-color: green; height: 80px; font-weight: bold;")
        self.btn_start.pressed.connect(lambda: self.start_tx("STARTMAIN"))
        self.btn_start.released.connect(self.stop_tx)
        layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("HOLD TO ESTOP")
        self.btn_stop.setStyleSheet("background-color: red; height: 80px; font-weight: bold;")
        self.btn_stop.pressed.connect(lambda: self.start_tx("ESTOP"))
        self.btn_stop.released.connect(self.stop_tx)
        layout.addWidget(self.btn_stop)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("background-color: black; color: #0f0;")
        layout.addWidget(self.log)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def generate_lora_packet(self, message):
        """The mathematical LoRa encoder from our previous session"""
        sf, bw, fs = 7, 125000, 1000000
        N = int(fs * (2 ** sf / bw))
        t = np.arange(N) / fs

        # Preamble + Sync
        up = np.exp(1j * np.pi * (bw / (2 ** sf / bw)) * (t ** 2))
        down = np.exp(-1j * np.pi * (bw / (2 ** sf / bw)) * (t ** 2))
        packet = [up] * 8 + [down, down, down[:int(N / 4)]]

        # RadioHead Header + Payload
        full_msg = "".join([chr(255), chr(255), chr(0), chr(0)]) + message
        for char in full_msg:
            val = ord(char) % (2 ** sf)
            shift_t = (np.arange(N) + (val * (N / 2 ** sf))) % N / fs
            packet.append(np.exp(1j * np.pi * (bw / (2 ** sf / bw)) * (shift_t ** 2)))

        return (np.concatenate(packet) * 2047).astype(np.complex64)

    def start_tx(self, msg):
        self.is_transmitting = True
        self.log.append(f"Sending {msg}...")
        threading.Thread(target=self.tx_loop, args=(msg,), daemon=True).start()

    def stop_tx(self):
        self.is_transmitting = False
        self.log.append("TX Stopped.")

    def tx_loop(self, msg):
        iq_data = self.generate_lora_packet(msg)
        while self.is_transmitting:
            self.worker.sdr.tx(iq_data)
            time.sleep(0.01)

    def update_rssi(self, text):
        self.rssi_label.setText(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GroundStation()
    window.show()
    sys.exit(app.exec())