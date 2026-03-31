import board
import busio
from digitalio import DigitalInOut
import adafruit_rfm9x
import sys
import time
from digitalio import Direction

from LanderMain import LanderMain

# Standard Startup Hardware Init
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs = DigitalInOut(board.CE0)
reset = DigitalInOut(board.D25)
rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 915)


reset.direction = Direction.OUTPUT
reset.value = False
time.sleep(0.01)
reset.value = True
time.sleep(0.01)

rfm9x.invert_iq = True
rfm9x.spreading_factor = 7
rfm9x.signal_bandwidth = 125000
rfm9x.coding_rate = 5  # This represents 4/5 in many LoRa libraries
rfm9x.low_data_rate_optimize = False # Match this to your GRC 'Off' setting
rfm9x.sync_word = 0x12 # Match your GRC '18' setting
rfm9x.enable_crc = False

lastRssi = 10000000.0 #starting value out of normal range

print("Pi Booted. Waiting for STARTMAIN signal from Pluto+...")
started = False
while not started:
    #print("Heartbeat...")
    packet = rfm9x.receive()
    if packet is None:
        # Print the background noise level every few seconds
        rssi = rfm9x.last_rssi
        if abs(lastRssi - rssi) > 1:
            print(f"Noise Floor: {rssi} dBm")
            lastRssi = rssi
    else:
        rssi = rfm9x.last_rssi
        if abs(lastRssi - rssi) > 1:
            print(f"Noise Floor: {rssi} dBm")
            lastRssi = rssi
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

print("Launching Main Program.")
lander = LanderMain(spi, cs, reset, rfm9x)
lander.runMainLoop()
print("Main Program finished!")

sys.exit(0)