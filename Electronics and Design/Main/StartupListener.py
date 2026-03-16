import board
import busio
from digitalio import DigitalInOut
import adafruit_rfm9x
import os, subprocess
import sys

from LanderMain import LanderMain

# Standard Startup Hardware Init
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs = DigitalInOut(board.CE0)
reset = DigitalInOut(board.D25)
rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 915)

rfm9x.invert_iq = True
rfm9x.spreading_factor = 7
rfm9x.signal_bandwidth = 125000
rfm9x.coding_rate = 5  # This represents 4/5 in many LoRa libraries
rfm9x.low_data_rate_optimize = False # Match this to your GRC 'Off' setting
rfm9x.sync_word = 0x12 # Match your GRC '18' setting

lastRssi = 0

print("Pi Booted. Waiting for STARTMAIN signal from Pluto+...")
started = False
while not started:
    packet = rfm9x.receive()
    if packet is None:
        # Print the background noise level every few seconds
        rssi = rfm9x.last_rssi
        if abs(lastRssi - rssi) > 5:
            print(f"Noise Floor: {rssi} dBm")
            lastRssi = rssi
    else:
        print("Packet Received!")
        # Convert bytes to string and strip whitespace/nulls
        print(f"Packet raw: , {packet}")
        packet_text = str(packet, "utf-8").strip()
        print(f"Decoded: [{packet_text}]")
        try:
            if packet_text == "STARTMAIN":
                print("Signal Received. ")
                started = True
                break

        except Exception as e:
            print(e)
            pass
'''
# Release the pins so the next script can use them
rfm9x.reset()  # Optional: Put radio in sleep/reset
spi.deinit()  # Release the SPI bus (SCK, MOSI, MISO)
cs.deinit()  # Release the Chip Select pin (CE0)
reset.deinit()

spi = None
cs = None
reset = None
rfm9x = None

# Execute Main and exit Listener
os.system("'/home/ARC/Github ARC/Lander-Challenge/Electronics and Design/venv/bin/python3' -u '/home/ARC/Github ARC/Lander-Challenge/Electronics and Design/Main/LanderMain.py' > '/home/ARC/Github ARC/Lander-Challenge/Electronics and Design/Main/mission.log' 2>&1 ")
#result = subprocess.run(["'/home/ARC/Github ARC/Lander-Challenge/Electronics and Design/venv/bin/python3' -u '/home/ARC/Github ARC/Lander-Challenge/Electronics and Design/Main/LanderMain.py' > '/home/ARC/Github ARC/Lander-Challenge/Electronics and Design/Main/mission.log' 2>&1 &"], capture_output=True, text=True)
#print(result.stdout)
'''
print("Launching Main Program.")
lander = LanderMain(spi, cs, reset, rfm9x)
lander.runMainLoop()
print("Main Program finished!")

sys.exit(0)