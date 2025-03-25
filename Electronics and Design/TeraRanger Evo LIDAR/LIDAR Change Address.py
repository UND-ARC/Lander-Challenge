import smbus2
import time

# Define the I2C bus (use 1 for Raspberry Pi)
I2C_BUS = 1
OLD_ADDRESS = 0x31  # Default I2C address of the TerraRanger Evo
NEW_ADDRESS = 0x40  # Replace with the desired new address (0x08 - 0x77)

# Register address for changing the I2C address (consult manufacturer datasheet)
CHANGE_ADDRESS_CMD = [0xA2, NEW_ADDRESS]  # Hypothetical command; check documentation

def change_i2c_address(bus, old_addr, new_addr):
    try:
        print(f"Connecting to device at I2C address: 0x{old_addr:X}")

        # Open I2C bus
        with smbus2.SMBus(bus) as smbus:
            # Send the address change command
            smbus.write_i2c_block_data(old_addr, CHANGE_ADDRESS_CMD[0], CHANGE_ADDRESS_CMD[1:])
            print(f"Sent command to change address to 0x{new_addr:X}")

            # Wait for changes to take effect
            time.sleep(1)

            # Verify new address works
            smbus.write_quick(new_addr)
            print(f"Address successfully changed to 0x{new_addr:X}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    change_i2c_address(I2C_BUS, OLD_ADDRESS, NEW_ADDRESS)
