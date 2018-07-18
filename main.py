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

SSID='Medils'
PASSWORD='1234561234'


print('starting up')
rider = Skroderider('test_new', debug=True)
print('initialized')

while True:
    ret = rider.setup(SSID, PASSWORD, '192.168.20.175',6301)
    if not ret:
        print('connection unsuccessful')
    else:
        print('sending')
        rider.send_data(1.0, 2.0, 3.0)
        print('sent')
        rider.disconnect()
        print('disconnected')
    time.sleep(10)

