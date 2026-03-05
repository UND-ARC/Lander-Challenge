import time
import sys
from RadioModule import LanderRadio
from GPSModule import LanderGPS


def main():
    radio = LanderRadio()
    gps = LanderGPS()

    print("Main Program Running. Monitoring for ESTOP...")

    try:
        while True:
            # 1. Check for Emergency Stop from Pluto+
            if radio.check_for_estop():
                print("ESTOP RECEIVED! Terminating vehicle functions.")
                sys.exit(0)

            # 2. Get and Send GPS Data
            location = gps.get_coords()
            radio.send_data(location)
            print(f"Broadcasting: {location}")

            time.sleep(1)

    except KeyboardInterrupt:
        print("Manual Shutdown")


if __name__ == "__main__":
    main()