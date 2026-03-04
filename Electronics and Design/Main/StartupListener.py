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

rfm9x.spreading_factor = 7
rfm9x.signal_bandwidth = 125000
rfm9x.coding_rate = 5  # This represents 4/5 in many LoRa libraries
rfm9x.low_data_rate_optimize = False # Match this to your GRC 'Off' setting
rfm9x.sync_word = 0x12 # Match your GRC '18' setting

print("Pi Booted. Waiting for STARTMAIN signal from Pluto+...")

while True:
    packet = rfm9x.receive() # Block until signal received
    if packet is None:
        # Print the background noise level every few seconds
        print(f"Noise Floor: {rfm9x.last_rssi} dBm")
    else:
        print("Packet Received!")
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