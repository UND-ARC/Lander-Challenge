import board
import busio
from digitalio import DigitalInOut
import adafruit_rfm9x

class LanderRadio:
    def __init__(self, freq=915.3):
        self.spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        self.cs = DigitalInOut(board.CE0)
        self.reset = DigitalInOut(board.D25)
        self.rfm9x = adafruit_rfm9x.RFM9x(self.spi, self.cs, self.reset, freq)
        self.rfm9x.tx_power = 23

    def send_data(self, message):
        self.rfm9x.send(bytes(message, "utf-8"))

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