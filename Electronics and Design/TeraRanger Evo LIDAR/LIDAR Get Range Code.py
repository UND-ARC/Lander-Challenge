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
with open('LIDARout.txt', 'w') as output:    
    while next == '':
        distance = read_distance()
        if (distance != None):
            print(f"Distance: {distance:.3f} m")
        else:
            print("Invalid reading")
        output.write(str(round(distance, 3)) + "\n")
        next = input('Continue? ')