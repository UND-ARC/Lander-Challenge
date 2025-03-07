import time
import sys
import matplotlib.pyplot as plt
import RPi.GPIO as GPIO
from hx711 import HX711

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
times = []
weights = []

startTime = time.perf_counter()

try:
    hx711 = HX711(5, 6)

    hx711.zero()   # Before we start, reset the HX711 (not obligate)
    while(time.perf_counter() - startTime < 20):
        read = hx711.get_data_mean()
        cTime = round(time.perf_counter() - startTime, 2)
        print("Weight:", read, "g", "Time:", cTime)
        times.append(cTime)
        weights.append(read/1000)
        #time.sleep(1)
        
finally:
    GPIO.cleanup()  # always do a GPIO cleanup in your scripts!
    print("done")
    fig1 = plt.figure()
    plt.plot(times, weights, 'blue')
    plt.xlabel('Time(seconds)')
    plt.ylabel('Weights(g)')
    plt.title('Weight vs Time')    
    plt.show()