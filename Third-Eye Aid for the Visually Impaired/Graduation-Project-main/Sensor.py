# This code will not be used as we do not possess the hardware in order for it to run.
# but this shows what the sensor code would be if we possessed the hardware.

import RPi.GPIO as GPIO
import time

# Set the GPIO numbering mode
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define the GPIO pin
trigger_pin = 3
echo_pin = 2

# Set up the GPIO pins
GPIO.setup(trigger_pin, GPIO.OUT)
GPIO.setup(echo_pin, GPIO.IN)

def measure_distance():
    # Ensure the trigger pin is low
    GPIO.output(trigger_pin, False)
    time.sleep(0.1)

    # Send a 10us pulse to start the measurement
    GPIO.output(trigger_pin, True)
    time.sleep(0.00001)  # 10 microseconds
    GPIO.output(trigger_pin, False)

    start_time = time.time()
    stop_time = time.time()

    # Save the start time
    while GPIO.input(echo_pin) == 0:
        start_time = time.time()

    # Save the time of arrival
    while GPIO.input(echo_pin) == 1:
        stop_time = time.time()

    # Time difference between start and arrival
    time_elapsed = stop_time - start_time
    # Multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (time_elapsed * 34300) / 2

    return distance

try:
    while True:
        dist = measure_distance()
        print(f"Measured Distance = {dist:.1f} cm")
        time.sleep(1)
except KeyboardInterrupt:
    print("Measurement stopped by user")
    GPIO.cleanup()
