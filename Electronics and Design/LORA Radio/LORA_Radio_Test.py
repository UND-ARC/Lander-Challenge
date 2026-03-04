import time
import board
import busio
import serial
import adafruit_gps
from digitalio import DigitalInOut
import adafruit_rfm9x

class LoRaRadio:
    def __init__(self):
        # 1. Setup GPS
        uart = serial.Serial("/dev/serial0", baudrate=9600, timeout=10)
        gps = adafruit_gps.GPS(uart, debug=False)
        # Turn on basic GGA and RMC info
        gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
        # Set update rate to 1Hz (recommended for initial testing)
        gps.send_command(b"PMTK220,1000")

        # Define frequency (Match this to your Pluto+ later)
        RADIO_FREQ_MHZ = 915.3
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
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
        print("Lander-Challenge: GPS to LoRa active...")

        while True:
            gps.update()

            # Check if we have a valid GPS fix
            if not gps.has_fix:
                msg = "Waiting for GPS fix..."
            else:
                # Format coordinates for the logger
                msg = f"Lat:{gps.latitude:.6f} Lon:{gps.longitude:.6f} Alt:{gps.altitude_m}m"

            # Send over LoRa
            rfm9x.send(bytes(msg, "utf-8"))
            print(f"Sent: {msg}")
            time.sleep(5)

if __name__ == "__main__":
    lora = LoRaRadio()