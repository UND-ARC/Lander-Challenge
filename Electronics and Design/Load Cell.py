import RPi.GPIO as GPIO
from hx711 import HX711

GPIO.setwarnings(False)

try:
    hx711 = HX711(
        dout_pin=5,
        pd_sck_pin=6,
        gain=64,
        channel='A'
    )

    hx711.reset()
    measures = hx711.get_raw_data(num_measures=3)

finally:
    GPIO.cleanup()

print("\n".join(measures))