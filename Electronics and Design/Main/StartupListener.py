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

# Try to lock the bus manually to see if it's alive
if spi.try_lock():
    print("SPI Bus is working and locked!")
    spi.configure(baudrate=5000000) # 5MHz
    spi.unlock()
else:
    print("SPI Bus is BUSY or LOCKED by another process!")

cs = DigitalInOut(board.CE0)
reset = DigitalInOut(board.D25)
rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 915)

# Force the radio to wake up and calibrate its RSSI circuit
rfm9x.idle()
time.sleep(0.1)
rfm9x.listen() # This is the command that actually turns on the 'ears'
# Force LNA to Max Gain (G1) and High Frequency Mode
# RegLna (0x0C) -> 0x23 (Max gain, default boost)
rfm9x._write_u8(0x0C, 0x23)
print(f"LNA Forced to: {rfm9x._read_u8(0x0C)}")
print(f"Radio Mode: {rfm9x.operation_mode}") # Should NOT be 0 (Sleep)


reset.direction = Direction.OUTPUT
reset.value = False
time.sleep(0.01)
reset.value = True
time.sleep(0.01)

rfm9x.invert_iq = False
rfm9x.spreading_factor = 7
rfm9x.signal_bandwidth = 125000
rfm9x.coding_rate = 5  # This represents 4/5 in many LoRa libraries
rfm9x.low_data_rate_optimize = False # Match this to your GRC 'Off' setting
rfm9x.sync_word = 0x12 # Match your GRC '18' setting
rfm9x.enable_crc = False

lastRssi = 10000000.0 #starting value out of normal range

print(f"Chip Version: {rfm9x._read_u8(0x42)}")

print("Pi Booted. Waiting for STARTMAIN signal from Pluto+...")
started = False
while not started:
    #print("Heartbeat...")
    packet = rfm9x.receive(timeout=0.5)
    rssi = rfm9x.last_rssi
    snr = rfm9x.last_snr
    #if abs(lastRssi - rssi) > 1:
    print(f"Noise Floor: {rssi} dBm | SNR: {snr}")
    raw_rssi = rfm9x._read_u8(0x1B)
    print(f"Raw Reg 0x1B: {raw_rssi}")
    lastRssi = rssi

    if packet is not None:

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