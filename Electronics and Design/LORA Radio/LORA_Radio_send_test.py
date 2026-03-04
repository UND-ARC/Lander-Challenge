import time
import busio
from digitalio import DigitalInOut
import board
import adafruit_rfm9x

# Define frequency (Match this to your Pluto+ later)
RADIO_FREQ_MHZ = 915.3



# Initialize SPI using the labeled pins on your cobbler
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

# Define pins based on your setup
cs = DigitalInOut(board.CE0)
reset = DigitalInOut(board.D25)

try:
    rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, RADIO_FREQ_MHZ)

    rfm9x.spreading_factor = 7  # Options: 7 to 12
    rfm9x.signal_bandwidth = 125000  # Options: 7800, 10400, 15600, 20800, 31250, 41700, 62500, 125000, 250000

    print("RFM95W found! Ready to transmit.")
except Exception as e:
    print(f"Hardware not found. Check if SPI is enabled and wires are tight.\n{e}")
    exit()

# Max power for initial testing
rfm9x.tx_power = 23

print("Broadcasting 'Hello World' to Pluto+...")

while True:
    data = bytes("Hello, World!\r\n", "utf-8")
    rfm9x.send(data)
    print("Packet sent!")
    time.sleep(2)