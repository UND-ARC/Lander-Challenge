import serial
import adafruit_gps

class LanderGPS:
    def __init__(self):
        self.uart = serial.Serial("/dev/serial0", baudrate=9600, timeout=10)
        self.gps = adafruit_gps.GPS(self.uart, debug=False)
        self.gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
        self.gps.send_command(b"PMTK220,1000")

    def get_coords(self):
        self.gps.update()
        if not self.gps.has_fix:
            return "No Fix"
        return f"Lat:{self.gps.latitude:.6f} Lon:{self.gps.longitude:.6f} Alt:{self.gps.altitude_m}m"