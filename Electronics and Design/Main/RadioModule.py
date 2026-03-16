import board
import busio
from digitalio import DigitalInOut
import adafruit_rfm9x

class LanderRadio:
    def __init__(self, spi, cs, reset, rfm9x):
        self.spi = spi
        self.cs = cs
        self.reset = reset
        self.rfm9x = rfm9x

        self.rfm9x.tx_power = 23

    def send_data(self, message):
        self.rfm9x.send(bytes(message, "utf-8"))
        print(f"Data sent: {message}")

    def check_for_estop(self):
        # Look for a packet without blocking the whole program
        packet = self.rfm9x.receive(timeout=0.1)
        if packet:
            try:
                msg = str(packet, "utf-8").strip()
                return msg == "ESTOP"
            except:
                return False
        return False