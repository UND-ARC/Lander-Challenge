import board, busio, digitalio, adafruit_rfm9x

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs  = digitalio.DigitalInOut(board.CE0)
rst = digitalio.DigitalInOut(board.D25)
rfm = adafruit_rfm9x.RFM9x(spi, cs, rst, 915.0)

rfm.spreading_factor = 7
rfm.signal_bandwidth = 125000
rfm.coding_rate      = 5
rfm._write_u8(0x39, 0x12)

# Read the version register — should return 0x12 if SPI is working
version = rfm._read_u8(0x42)
print(f"RFM95W version register: 0x{version:02X}  (expect 0x12)")

print("Listening...")
while True:
    pkt = rfm.receive(timeout=5.0)
    print("Packet!" if pkt else "Nothing in 5s...")