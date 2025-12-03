from labjack import ljm
import time, csv

h = ljm.openS("T4", "USB", "ANY")
ljm.eWriteName(h, "DAC0", 2.5)
print("set DAC0 to 2.5")
vout = ljm.eReadName(h, "DAC0")
print("DAC0 actually reads:", vout, "V")

vin = ljm.eReadName(h, "AIN0")

with open("log.csv", "a", newline="") as f:
    w = csv.writer(f)
    while True:
        w.writerow([time.time(), vout, vin])
        f.flush()
        time.sleep(0.5)

ljm.close(h)