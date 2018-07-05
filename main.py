import analogio
import board
import digitalio
import time
import sys
from skroderider import Skroderider

try:
    import struct
except ImportError:
    import ustruct as struct

SSID='castleinthesky_2.4GHz'
PASSWORD='OV8ieghaijah0vik'

MAX_VAL = 65535

light_pin = analogio.AnalogIn(board.A0)
temperature_pin = analogio.AnalogIn(board.A1)
humidity_pin = analogio.AnalogIn(board.A2)

def get_temperature(temp_pin):
    u_out = (temp_pin.value / float(MAX_VAL))*temp_pin.reference_voltage*1000.
    temp = (u_out - 500.) / 10.
    return temp

def get_light(light_pin, u_in=3.3):
    u_out = (light_pin.value / MAX_VAL)*light_pin.reference_voltage
    pullup = 10000.
    return pullup*(u_in - u_out)/u_out

def get_humidity(humidity_pin):
    u_out = (humidity_pin.value / float(MAX_VAL))*humidity_pin.reference_voltage*1000.
    humidity = (u_out - 500.) / 10.
    return humidity


names = ['sunflower', 'tulip', 'forgetmenot', 'baobab']

rider = Skroderider('sunflower')
ret = rider.setup(SSID, PASSWORD, '192.168.1.163',6301) 
print(ret)
while True:

    temp = get_temperature(temperature_pin)
    light = get_light(light_pin)
    humidity = get_humidity(humidity_pin)
    rider.send_data(light, temp, humidity)
    time.sleep(5)
