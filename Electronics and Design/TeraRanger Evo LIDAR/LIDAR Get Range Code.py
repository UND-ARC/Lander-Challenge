import smbus
import time

I2C_BUS = 1
I2C_ADDRESS = 0x31

bus = smbus.SMBus(I2C_BUS)

def read_distance():
    try:
        data = bus.read_i2c_block_data(I2C_ADDRESS, 0, 2)

        distance = (data[0] << 8 | data[1])

        if (distance == 65535):
            return None
        return distance / 1000.0
    
    except Exception as e:
        print(f"Error reading from sensor: {e}")
        return None
next = ''
with open('LIDARfar.txt', 'w') as output:    
    while next == '':
        distance = round(read_distance(), 3)
        if (distance != None):
            print(f"Distance: {distance:.3f} m")
        else:
            print("Invalid reading")
        output.write("Meters: " + str(distance) + " Feet: " + str(distance*3.28) + " Inches: " + str(distance*3.28/12) + "\n")
        next = input('Continue? ')