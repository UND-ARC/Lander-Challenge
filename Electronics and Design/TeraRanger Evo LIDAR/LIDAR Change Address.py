import smbus
import time

I2C_BUS = 1  # Raspberry Pi's I2C bus
CURRENT_ADDRESS = 0x31  # Default Teraranger Evo I2C address
NEW_ADDRESS = 0x30  # Change this to the desired address (7-bit format)

bus = smbus.SMBus(I2C_BUS)

def change_i2c_address(current_addr, new_addr):
    try:
        # Convert to valid range (7-bit I2C address)
        if new_addr < 0x08 or new_addr > 0x77:
            print("Error: Address out of valid range (0x08 - 0x77)")
            return
        
        # Send the new address command (Terabee-specific protocol)
        COMMAND_SET_I2C_ADDR = [0x00, new_addr << 1]  # New address shifted left for 8-bit format
        bus.write_i2c_block_data(current_addr, 0x00, COMMAND_SET_I2C_ADDR)

        print(f"Sent command to change I2C address to: {hex(new_addr)}")

        time.sleep(1)  # Give time for the change to take effect

        # Verify the change
        new_detected = False
        for _ in range(3):
            time.sleep(0.5)
            detected_addresses = []
            for addr in range(0x08, 0x78):
                try:
                    bus.read_byte(addr)
                    detected_addresses.append(hex(addr))
                except:
                    pass
            if hex(new_addr) in detected_addresses:
                print(f"New address {hex(new_addr)} detected!")
                new_detected = True
                break

        if not new_detected:
            print("Error: Address change not successful. Power cycle the sensor and try again.")

    except Exception as e:
        print(f"Error changing address: {e}")

if __name__ == "__main__":
    change_i2c_address(CURRENT_ADDRESS, NEW_ADDRESS)