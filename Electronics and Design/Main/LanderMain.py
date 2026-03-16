import time
import sys
from RadioModule import LanderRadio
from GPSModule import LanderGPS

class LanderMain:
    def __init__(self, spi, cs, reset, rfm9x):
        print("Main Program Running. Monitoring for ESTOP...")
        self.radio = LanderRadio(spi, cs, reset, rfm9x)
        self.gps = LanderGPS()

    def runMainLoop(self):
        try:
            while True:
                # 1. Check for Emergency Stop from Pluto+
                self.check_for_estop()

                # 2. Get and Send GPS Data
                data = ""
                data = data + "GPS: " + str(self.get_gps())

                self.radio.send_data(data)

                time.sleep(1)

        except KeyboardInterrupt:
            print("Manual Shutdown")

    def check_for_estop(self):
        if self.radio.check_for_estop():
            print("ESTOP RECEIVED! Terminating vehicle functions.")
            sys.exit(0)

    def get_gps(self):
        location = self.gps.get_coords()
        return location






def main():







if __name__ == "__main__":
    main()