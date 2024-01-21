#!/usr/bin/python
import time
import board
import adafruit_scd30
import busio
from gpiozero import LED, Button
import threading
from datetime import datetime
import sys
#sys.path.append('/path/to/this/script') #add it in case you want to run this script automaticaly on raspberry booting

from signal import pause
import os

# Initialize I2C and sensor
i2c = busio.I2C(board.SCL, board.SDA, frequency=10000)
scd = adafruit_scd30.SCD30(i2c)

write_lock = threading.Lock()
button_recently_pressed = threading.Event()
button_recently_pressed.clear() 
current_measurement_thread = None
stop_measurement = threading.Event()
# File setup
file_path = '/home/pi/ilja/my_stuff/temp_humidity_co2_logger.txt'
if not os.path.exists(file_path):
    with open(file_path, 'w') as f:
        f.write('SCD30 sensor\ndate, co2, temperature_C, relative_humidity,comment\n')

# LED and Button setup
led_yellow_pin = 21
button_red_pin = 20
led_red_pin = 26
button_green_pin = 19
led_green_pin = 13
led_yellow = LED(led_yellow_pin)
button_red = Button(button_red_pin)
button_green = Button(button_green_pin)
led_green = LED(led_green_pin)
led_red = LED(led_red_pin)


def led_yellow_shine_on_measurement():
    led_yellow.on()
    time.sleep(3)
    led_yellow.off()

def led_green_shine():
    led_green.on()
    time.sleep(3)
    led_green.off()

def led_red_shine():
    led_red.on()
    time.sleep(3)
    led_red.off()

def record_measurement(comment="None"):
    global write_lock
    print("Making measurement, hold on..")
    print(datetime.now().isoformat())
    try:
        print(comment)
        if scd.data_available:
            threading.Thread(target=led_yellow_shine_on_measurement).start()
            timestamp = datetime.now()
            print("Time: ",timestamp.isoformat())
            print(f"Co2: {scd.CO2},Temp: {scd.temperature},Rel. hum: {scd.relative_humidity},Comment: {comment}\n")
            with write_lock:
                with open(file_path, 'a') as f:
                    f.write(f"{timestamp.isoformat()},")
                    f.write(f"{scd.CO2},{scd.temperature},{scd.relative_humidity},{comment}\n")
    except RuntimeError: #CRC,quite often throws an error, because checked value is not valid
        with write_lock:
                with open(file_path, 'a') as f:
                    f.write(f"{timestamp.isoformat()},")
                    f.write(f"None,None,None,{comment}\n")

def start_measurement_thread(interval, duration):
    global current_measurement_thread
    if current_measurement_thread is not None:
        stop_measurement.set()  
        current_measurement_thread.join()  

    current_measurement_thread = threading.Thread(target=record_interval_after_button, args=(interval, duration))
    current_measurement_thread.start()

def button_red_pressed():
    button_red.wait_for_inactive(0.5)
    print("Window was closed")
    threading.Thread(target=led_red_shine).start()
    record_measurement(comment="closed")
    start_measurement_thread(60, 30*60) # each 60 seconds per 30 minutes range 

def button_green_pressed():
    button_green.wait_for_inactive(0.5)
    print("Window was opened")
    threading.Thread(target=led_green_shine).start()
    record_measurement(comment="opened")
    start_measurement_thread(60, 30*60)# each 60 seconds per 30 minutes range 

def record_interval_measurements(interval):
    while True:
        record_measurement()
        time.sleep(interval)

def record_interval_after_button(interval, time_sec_frequent_measurements):
    stop_measurement.clear()
    start_time = time.time()
    while not stop_measurement.is_set() and (time.time() - start_time < time_sec_frequent_measurements):
        record_measurement()
        time.sleep(interval)
threading.Thread(target=record_interval_measurements,args=(60*5,)).start()
button_red.when_pressed = button_red_pressed
button_green.when_pressed = button_green_pressed
pause() 
