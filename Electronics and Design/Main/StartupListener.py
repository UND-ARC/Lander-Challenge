import board
import busio
from digitalio import DigitalInOut
import adafruit_rfm9x
import subprocess
import sys

# Standard Startup Hardware Init
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs = DigitalInOut(board.CE0)
reset = DigitalInOut(board.D25)
rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 915.3)

print("Pi Booted. Waiting for STARTMAIN signal from Pluto+...")

while True:
    packet = rfm9x.receive(timeout=None) # Block until signal received
    if packet:
        try:
            msg = str(packet, "utf-8").strip()
            if msg == "STARTMAIN":
                print("Signal Received. Launching Main Program.")
                # Execute Main and exit Listener
                subprocess.Popen(["python3", "/home/jacob/Code/LanderMain.py"])
                sys.exit(0)
        except:
            pass