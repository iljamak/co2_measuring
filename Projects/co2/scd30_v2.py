import time
import board
import adafruit_scd30
import busio
from gpiozero import LED, Button
import threading
from datetime import datetime
from timed_input import input_with_timeout,TimeoutExpired
from signal import pause
import os

# Initialize I2C and sensor
i2c = busio.I2C(board.SCL, board.SDA, frequency=50000)
scd = adafruit_scd30.SCD30(i2c)

write_lock = threading.Lock()
measuring_lock = threading.Lock()
# File setup
file_path = 'temp_humidity_co2_logger.txt'
if not os.path.exists(file_path):
    with open(file_path, 'w') as fp:
        fp.write('SCD30 sensor\ndate, co2, temperature_C, relative_humidity,comment\n')

# LED and Button setup
led_pin = 21
button_pin = 20
led = LED(led_pin)
button = Button(button_pin)

# Measurement control
is_measuring = threading.Event()
is_measuring.clear()  # Start with measurement off

def led_shine_on_measurement():
    led.on()
    time.sleep(3)
    led.off()

def record_measurement(comment="None"):
    global write_lock
    print("Making measurement, hold on..")
    print(comment)
    if scd.data_available:
        threading.Thread(target=led_shine_on_measurement).start()
        timestamp = datetime.now()
        with write_lock:
            with open(file_path, 'a') as f:
                f.write(f"{timestamp.isoformat()},")
                f.write(f"{scd.CO2},{scd.temperature},{scd.relative_humidity},{comment}\n")

def user_input_thread():
    global is_measuring
    try:
        comment = input_with_timeout("[C]losing, else opneing will be activated", 10)
        if comment.strip().lower():
            record_measurement(comment="closing")
        else:
            record_measurement(comment="opening")
    except TimeoutExpired:
        record_measurement(comment="opening")
    finally:
        is_measuring.clear()  # Clear the measurement flag
        measuring_lock.release()  # Release the lock
def button_pressed():
    button.wait_for_inactive(0.5)
    global is_measuring
    if not measuring_lock.locked():  # Check if another measurement is not already running
        print("Starting measurements activated by button...")
        measuring_lock.acquire()  # Acquire the lock
        is_measuring.set()  # Indicate that a measurement is in progress
        user_input = threading.Thread(target=user_input_thread)
        user_input.start()
    else:
        print("NOT NOT")
def record_interval_measurements(interval):
    while True:
        if is_measuring.is_set():
            time.sleep(interval)  # Skip automated measurement if manual measurement is in progress
            continue
        record_measurement()
        time.sleep(interval)


threading.Thread(target=record_interval_measurements,args=((900,))).start()
button.when_pressed = button_pressed

pause()  # Keep the program running
