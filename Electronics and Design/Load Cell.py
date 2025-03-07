import time
import sys
import matplotlib.pyplot as plt
import RPi.GPIO as GPIO
from hx711 import HX711

GPIO.setwarnings(False)
times = []
weights = []

startTime = time.perf_counter()

try:
    hx711 = HX711(
            dout_pin=5,
            pd_sck_pin=6,
            channel='A',
            gain=64
        )

    hx711.reset()   # Before we start, reset the HX711 (not obligate)
    while(True):
        print("Weight:", hx711.get_raw_data(1), "g", "Time:", round((time.perf_counter() - startTime), 2))
        times.append(time.perf_counter() - startTime)
        weights.append(hx711.get_raw_data()/1000)
        time.sleep(1)
        
finally:
    GPIO.cleanup()  # always do a GPIO cleanup in your scripts!
    fig1 = plt.figure()
    plt.plot(times, weights, 'blue')
    plt.xlabel('Time(seconds)')
    plt.ylabel('Weights(kg)')
    plt.title('Weight vs Time')    
