import serial
import pexpect
import elf_parser
import re
import shlex, subprocess
import time

class LEDTimingTimeout(Exception):
    pass

class InterrogatorInterface:
    def __init__(self):
        self.ser = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=10)
        self.ser.setBaudrate(9600)
        self.ser.setBaudrate(115200)
        self.comms_test()

    def wait_for_OK(self):
        all_received = []
        while True: # keep adding the received line to the array until the received line is OK
            received = self.ser.readline()
            if received == "OK\r\n".encode():
                return all_received
            if received == b'':
                raise Exception("Did not get OK from interrogator. Rather got: {r}.".format(r=all_received))
            all_received.append(received)
    
    def assert_response(self, expected):
        response = self.wait_for_OK()
        if response[1].strip().decode() !=  expected:
            raise Exception("Did not get response: {e}. Rather got: {r}".format(e=expected, r=response))

    def comms_test(self):
        self.ser.flushInput()
        self.ser.write("PING 1\r".encode())
        self.assert_response("PONG!")
        return "Communications with interrogator established"

    def reset(self, state):
        self.ser.flushInput()
        self.ser.write("NRST {}\r".format(state).encode())
        self.wait_for_OK()

    def set_pin(self, pin):
        self.ser.flushInput()
        self.ser.write("GPIO_SET {p}\r".format(p = pin).encode())
        self.wait_for_OK()
    def clear_pin(self, pin):
        self.ser.flushInput()
        self.ser.write("GPIO_CLEAR {p}\r".format(p = pin).encode())
        self.wait_for_OK()
    def highz_pin(self, pin):
        self.ser.flushInput()
        self.ser.write("GPIO_HIGHZ {p}\r".format(p = pin).encode())
        self.wait_for_OK()

    def write_port(self, port):
        pass
    def read_pin(self, pin):
        pass
    def read_port(self, port):
        self.ser.flushInput()
        self.ser.write("GPIO_READ 0\r".encode())
        resp = self.wait_for_OK() #something like: [b'GPIO_READ 0\r\n', b'INPUTS: AA\r\n', b'> ']
        try:
            assert(resp[0] == b'GPIO_READ 0\r\n') 
        except:
            raise Exception(resp[0])
        inputs = resp[1] # something like:  b'INPUTS: AA\r\n'
        inputs = inputs.split() # [b'INPUTS:', b'AA']
        return int(inputs[1], 16)

    def pattern_timing(self, pattern0, pattern1):
        pattern0 = pattern0 & 0xFF
        pattern1 = pattern1 & 0xFF
        self.ser.flushInput()
        # the opcode consists of two bytes: the lower byte must be pattern0, the upper byte must be pattern1
        self.ser.write("PATTERN_TIMING {p}\r".format(p = (pattern0) + (pattern1 << 8)).encode())
        resp = self.wait_for_OK() # something like: [b'PATTERN_TIMING 0xAA5\r\n5', b'TIMING: 23889736\r\n']
        cycles = int(resp[1].split()[1]) # second line, second word.
        if cycles == -1:
            return -1 # could not find patterns
        else:
            return cycles/48e6 # running at 48 MHz

    def timing_transition(self, pattern0, pattern1):
        """ Waits for the p0 -> p1 transition to occur and then
        times how long p1 stays on the LEDs
        """
        pattern0 = pattern0 & 0xFF
        pattern1 = pattern1 & 0xFF
        self.ser.flushInput()
        # the opcode consists of two bytes: the lower byte must be pattern0, the upper byte must be pattern1
        self.ser.write("PATTERN_TRANSITION {p}\r".format(p = (pattern0) + (pattern1 << 8)).encode())
        resp = self.wait_for_OK() # something like: [b'PATTERN_TIMING 0xAA5\r\n5', b'TIMING: 23889736\r\n']
        cycles = int(resp[1].split()[1]) # second line, second word.
        if cycles == -1:
            raise LEDTimingTimeout()
        else:
            return cycles/48e6 # running at 48 MHz

    def write_dac(self, channel, value):
        if (channel != 0) and (channel != 1):
            raise Exception("Invalid DAC channel")
        if (value < 0) or (value > 255):
            raise Exception("DAC value out of bounds")
        self.ser.flushInput()
        self.ser.write("DAC {val:#x}\r".format(val = ((channel << 8) + value)).encode())
        self.wait_for_OK()
