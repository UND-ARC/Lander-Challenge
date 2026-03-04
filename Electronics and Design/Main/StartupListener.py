import time
import board
import busio
from digitalio import DigitalInOut
import adafruit_rfm9x
import subprocess
import os
import signal

# Hardware Settings
RADIO_FREQ_MHZ = 915.3
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs = DigitalInOut(board.CE0)
reset = DigitalInOut(board.D25)
rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, RADIO_FREQ_MHZ)

main_process = None  # Variable to store the running program

print("Lander Manager: Listening for commands...")

while True:
    packet = rfm9x.receive(timeout=1.0)

    if packet is not None:
        try:
            message = str(packet, "utf-8").strip()
            print(f"Received Command: {message}")

            # --- START LOGIC ---
            if message == "START_MISSION":
                if main_process is None or main_process.poll() is not None:
                    print("Launching Lander-Challenge Main Program...")
                    # Update this path to your actual main script
                    main_process = subprocess.Popen(["python3", "LanderMain.py"])
                else:
                    print("Mission already running.")

            # --- END LOGIC ---
            elif message == "END_MISSION":
                if main_process and main_process.poll() is None:
                    print("Stopping Mission...")
                    # Send SIGTERM to stop the process gracefully
                    main_process.terminate()
                    main_process.wait()  # Wait for it to actually close
                    main_process = None
                    print("Mission stopped successfully.")
                else:
                    print("No active mission to stop.")

        except Exception as e:
            print(f"Command Error: {e}")

    time.sleep(0.1)