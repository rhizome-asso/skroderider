import board
import busio
import neopixel
import time

try:
    import struct
except ImportError:
    import ustruct as struct

CONNECT_RETRIES = 3

class Skroderider:

    def _scan_response(self, ok='OK', err='ERROR', debug=False):
        answer = ''
        while True:
            data = self.uart.read(32)
            if data is not None:
                answer += ''.join([chr(b) for b in data])
                if answer.endswith(ok+'\r\n'):
                    if debug:
                        return True, answer
                    else:
                        return True
                elif answer.endswith(err+'\r\n'):
                    if debug:
                        return False, answer
                    else:
                        return False

    def __init__(self, name, debug=False):
        self.wifi = False
        self.udp = False
        self.debug = debug
        self.name = name
        self.ssid = ''
        self.pwd = ''
        self.uart = busio.UART(board.TX, board.RX, baudrate=115200)

        self.dot = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.1)
        self.dot[0] = [0, 0, 255]
        time.sleep(0.3)
        self.dot[0] = [0, 0, 0]
        nb = self.uart.write('AT+RST\r\n')
        if self.debug:
            success, answer = self._scan_response(ok='ready', debug=True)
            print('DEBUG:',answer)
        else:
            success = self._scan_response(ok='ready')
        if not success:
            raise RuntimeError
        nb = self.uart.write('AT+CWMODE_CUR=1\r\n')
        if self.debug:
            success, answer = self._scan_response(debug=True)
            print('DEBUG:',answer)
        else:
            success = self._scan_response()
        if not success:
            self.dot[0] = [255, 0, 0]
            raise RuntimeError

    def _connect_wifi(self):
        for retry in range(CONNECT_RETRIES):
            nb = self.uart.write('AT+CWJAP_CUR="{ssid}","{pwd}"\r\n'.format(ssid=self.ssid, pwd=self.pwd))
            if self.debug:
                success, answer = self._scan_response(debug=True)
                print('DEBUG:',answer)
            else:
                success = self._scan_response()
            if success:
                self.dot[0] = [0, 0, 255]
                time.sleep(0.3)
                self.dot[0] = [0, 0, 0]
                self.wifi = True
                break
        if not success:
            self.dot[0] = [255, 0, 0]
            time.sleep(0.8)
            self.dot[0] = [0, 0, 0]
        return success

    def _prepare_udp(self):
        nb = self.uart.write('AT+CIPMUX=1\r\n')
        if self.debug:
            self.udp, answer = self._scan_response(debug=True)
            print('DEBUG:',answer)
        else:
            self.udp = self._scan_response()
        if not self.udp:
            return False
        nb = self.uart.write('AT+CIPSTART=0,"UDP","{ip}",{port}\r\n'.format(ip=self.ip, port=self.port))
        if self.debug:
            self.udp, answer = self._scan_response(debug=True)
            print('DEBUG:',answer)
        else:
            self.udp = self._scan_response()
        return self.udp

    def setup(self, ssid, pwd, ip, port):
        if self.wifi and ssid == self.ssid:
            if self.udp and ip == self.ip and port == self.port:
                if self.debug:
                    print('already setup')
                return True
            else:
                self.ip = ip
                self.port = port
                return self._prepare_udp()
        else:
            self.ssid = ssid
            self.pwd = pwd
            self.ip = ip
            self.port = port
            self._connect_wifi()
            self._prepare_udp()
        return self.wifi and self.udp

    def disconnect(self):
        if not self.wifi:
            return False
        if self.udp:
            nb = self.uart.write('AT+CIPCLOSE=0\r\n')
            if self.debug:
                success, answer = self._scan_response(debug=True)
                print('DEBUG:',answer)
            else:
                success = self._scan_response()
        if success:
            self.udp = False
        nb = self.uart.write('AT+CWQAP\r\n')
        if self.debug:
            success, answer = self._scan_response(ok='DISCONNECT', debug=True)
            print('DEBUG:',answer)
        else:
            success = self._scan_response(ok='DISCONNECT')
        if success:
            self.dot[0] = [0, 0, 255]
            time.sleep(0.3)
            self.dot[0] = [0, 0, 0]
            self.wifi = False
            return True
        else:
            self.dot[0] = [255, 0, 0]
            time.sleep(0.8)
            self.dot[0] = [0, 0, 0]
            return False

    def send_data(self, light, temp, humidity):
        nname = len(self.name)
        nb_exp = 4 + 4 + 4 + 4 + 1 + nname
        nb = self.uart.write('AT+CIPSEND=0,{}\r\n'.format(nb_exp))
        data = struct.pack('4s3fB{}s'.format(nname),
                           'DATA', light, temp, humidity, nname, self.name)
        nb = self.uart.write(data)
        if self.debug:
            success, answer = self._scan_response(debug=True)
            print('DEBUG:',answer)
        else:
            success = self._scan_response()
        if success:
            self.dot[0] = [0, 255, 0]
            time.sleep(0.3)
            self.dot[0] = [0, 0, 0]
        else:
            self.dot[0] = [255, 0, 0]
            time.sleep(0.8)
            self.dot[0] = [0, 0, 0]
        return success