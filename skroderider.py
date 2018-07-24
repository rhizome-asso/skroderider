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
    """Skroderider is an abstraction layer for ESP8266 AT based wifi+UDP communication. It uses AT commands
    as described here: https://www.espressif.com/sites/default/files/documentation/4a-esp8266_at_instruction_set_en.pdf
    and here: https://www.espressif.com/sites/default/files/documentation/4b-esp8266_at_command_examples_en.pdf
    """

    def _scan_response(self, ok='OK', err='ERROR', debug=False):
        """Read AT response from ESP8266 coming from uart and scan for ok.

        Arguments:
        ok    -- the return status string to scan for (default: 'OK')
        err   -- an alternative error status string to scan for (default: 'ERROR')
        debug -- control whether all returned characters should be forwarded as a second
                 return argument.
        """
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
        """Create a skroderider instance with a name.
        The name will be sent along with all UDP messages. Optionally the instance can
        be created in debug mode, increasing its verbosity.
        """
        self.wifi = False
        self.udp = False
        self.debug = debug
        self.name = name
        self.ssid = ''
        self.pwd = ''
        # initialzie uart (assuming this has not been done outside
        # @todo better to pass this as an argument
        self.uart = busio.UART(board.TX, board.RX, baudrate=115200)
        # initialize neopixel and blink briefly blue
        self.dot = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.1)
        self.dot[0] = [0, 0, 255]
        time.sleep(0.3)
        self.dot[0] = [0, 0, 0]
        # reset the device
        nb = self.uart.write('AT+RST\r\n')
        if self.debug:
            # for the AT+RST command we expect to get a "ready" instead of the typical "OK"
            # as a response
            success, answer = self._scan_response(ok='ready', debug=True)
            print('DEBUG:',answer)
        else:
            success = self._scan_response(ok='ready')
        if not success:
            self.dot[0] = [255, 0, 0]
            raise RuntimeError  # no use continuing
        # make sure we are in Station mode
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
        """Internal method for connecting to desired wifi network"""
        # allow several retries, once succeeded break, otherwise finish loop and return False
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
        """Internal method for setting up UDP."""
        # sets up connection multiplexing (allows mutliple connections to be maintained
        # at the same time. Not strictly needed here, but works.
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
        """Main API call for setting up the WiFi connection and registering target host
        for datagram transmission"""
        # first check if we need to do anything
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

    def reset(self):
        """Reset ESP8266 device. Using this regularly may help with stability issues"""
        nb = self.uart.write('AT+RST\r\n')
        if self.debug:
            success, answer = self._scan_response(ok='ready', debug=True)
            print('DEBUG:',answer)
        else:
            success = self._scan_response(ok='ready')
        return success

    def disconnect(self):
        """Deregister UDP target and disconnect from Wifi."""
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
        success = success and self.reset()
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
        """Send a skroderider DATA packet. The packet contains sensor data along with the
        skroderider client name.

        Arguments:
        light   -- a float representing the light sensor measurement
        temp    -- a float representing the temperature sensor measurement
        humdity -- a float representing a humidity / moisture sensor measrument
        """
        nname = len(self.name)
        # calculate size of packet
        nb_exp = 4 + 4 + 4 + 4 + 1 + nname
        # announce size of packet to ESP8266
        nb = self.uart.write('AT+CIPSEND=0,{}\r\n'.format(nb_exp))
        # pack data into structured byte buffer
        data = struct.pack('4s3fB{}s'.format(nname),
                           'DATA', light, temp, humidity, nname, self.name)
        # send data over uart to ESP
        nb = self.uart.write(data)
        # check if it worked
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