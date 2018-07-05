import board
import busio

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

    def __init__(self, name):
        self.wifi = False
        self.udp = False
        self.name = name
        self.ssid = ''
        self.pwd = ''
        self.uart = busio.UART(board.TX, board.RX, baudrate=115200)

        nb = self.uart.write('AT+RST\r\n')
        successful = self._scan_response(ok='ready')

        if not successful:
            raise RuntimeError

    def _connect_wifi(self):
        for retry in range(CONNECT_RETRIES):
            nb = self.uart.write('AT+CWJAP_CUR="{ssid}","{pwd}"\r\n'.format(ssid=self.ssid, pwd=self.pwd))
            success = self._scan_response()
            if success:
                self.wifi = True
                break
        return success

    def _prepare_udp(self):
        nb = uart.write('AT+CIPSTART=0,"UDP","{ip}",{port}\r\n'.format(ip=self.ip, port=self.port))
        self.udp = self._scan_response(ok='OK')
        return self.udp

    def setup(self, ssid, pwd, ip, port):
        if self.wifi and ssid == self.ssid:
            if self.udp and ip = self.ip and port = self.port:
                return True
            else:
                self.ip = ip
                self.port = port
                return self._prepare_udp()
        else:
            self.ssid = ssid
            self.pwd = pwd
            return self._connect_wifi()

    def send_data(self, light, temp, humidity):
        nname = len(self.name)
        nb_exp = 4 + 4 + 4 + 4 + 1 + nname
        nb = self.uart.write('AT+CIPSEND=0,{}\r\n'.format(nb_exp))
        data = struct.pack('4s3fB{}s'.format(nname),
                           'DATA', light, temp, humidity, nname, name)
        nb = uart.write(data)
        return self._scan_response()
