import serial
import pexpect
import elf_parser
import re
import shlex, subprocess
import time

class OpenOCD:
    def __init__(self, comment):
        self.comment = comment
        comment("Attempting to launch OpenOCD")
        openocdcmd = shlex.split("openocd -f interface/stlink-v2.cfg -f target/stm32f0x_stlink.cfg -c init -c \"reset halt\"")
        self.openocd = subprocess.Popen(openocdcmd, stderr=subprocess.DEVNULL)
        time.sleep(0.5)
        if self.openocd.poll() == None:
            comment("OpenOCD running")
        else:
            raise Exception("OpenOCD not running, but should be")
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        self.openocd.kill()
    def poll(self):
        return self.openocd.poll()

class GDBInterface:
    def __init__(self, fi, comment):
        self.comment = comment
        self.fi = fi
        self.gdb = pexpect.spawn("arm-none-eabi-gdb", timeout=3)
        self.gdb.expect_exact("(gdb)")
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        self.gdb.terminate(True)

    def open_file(self):
        self.gdb.sendline("file \"{}\"".format(self.fi))
        # we'll either get a done or a no such file
        if self.gdb.expect(["done.*\(gdb\)", "No such file or directory"]) == 0:
            self.comment( "file {} opened in GDB".format(self.fi))
        else:
            raise Exception("FATAL: Could not open file {} in GDB".format(self.fi))

    def connect(self):
        self.gdb.sendline("target remote localhost:3333")
        if self.gdb.expect(["Remote debugging using.*\(gdb\)", "Connection timed out"]) == 0:
            self.comment("GDB connected to openOCD")
        else:
            raise Exception("FATAL: GDB could not connect to openOCD\r\n")

    def soft_reset(self):
        self.comment("Attempting soft reset.")
        self.gdb.sendline("monitor reset halt")
        self.gdb.expect("target state: halted.*\(gdb\)")
        self.comment("Soft reset complete.")

    def erase(self):
        self.gdb.sendline("monitor flash erase_sector 0 0 0")
        self.gdb.expect("erased sectors 0 through 0 on flash bank 0 in.*\(gdb\)")
        self.comment("Microcontroller flash memory erased")

    def load(self):
        self.gdb.sendline("load")
        self.gdb.expect("Transfer rate.*\(gdb\)")
        self.comment(".elf file loaded into flash")

    def send_continue(self):
        self.comment("Continuing code")
        self.gdb.sendline("continue")
        self.gdb.expect_exact("Continuing.")
        self.comment("Code now running.")

    def send_control_c(self):
        self.comment("Sending Ctrl+C")
        self.gdb.sendcontrol('c')
        self.gdb.expect_exact("(gdb)")

    def run_to_label(self, label):
        # improve this with custom exceptions!!!!
        try:
            address = elf_parser.get_address_of_label(self.fi, label) # this will throw an exception if label not found
        except:
            self.comment("Could not find label: {l}".format(l = label))
            return False
        self.comment("Attempting to run to label {l} with address {a:#X}".format(l = label, a = address))
        self.comment("break *{a:#X}".format(a = address))
        self.gdb.sendline("break *{a:#x}".format(a = address))
        try:
            self.gdb.expect_exact("(gdb)")
            self.gdb.sendline("continue")
            self.gdb.expect("Breakpoint.*\(gdb\)")
            self.comment("Hit breakpoint")
            self.delete_all_breakpoints()
            return True
        except:
            self.comment("Breakpoint never hit. Code may have hard-faulted, or stuck in a loop?")
            self.send_control_c()
            return False

    def read_word(self, address):
        self.gdb.sendline("x/1wx {a:#x}".format(a = address))
        self.gdb.expect_exact("{0:#x}:".format(address))
        self.gdb.expect_exact("(gdb)")
        return int(self.gdb.before.strip(), 16)

    def write_word(self, address, data):
        set_string = "set {{int}}{a:#x} = {d:#x}".format(a = address, d = data)
        self.gdb.sendline(set_string)
        self.gdb.expect_exact("{}\r\n(gdb)".format(set_string))
    
    def delete_all_breakpoints(self):
        self.gdb.sendline("delete")
        self.gdb.expect_exact("Delete all breakpoints? (y or n) ")
        self.gdb.sendline("y")
        self.gdb.expect_exact("(gdb)")
        self.comment("All previous breakpoints deleted")

class InterrogatorInterface:
    def __init__(self):
        self.ser = serial.Serial("/dev/ttyS0", 115200, timeout=20)

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
        assert(resp[0] == b'GPIO_READ 0\r\n') 
        inputs = resp[1] # something like:  b'INPUTS: AA\r\n'
        inputs = inputs.split() # [b'INPUTS:', b'AA']
        return int(inputs[1], 16)

    def pattern_timing(self, pattern0, pattern1):
        self.ser.flushInput()
        # the opcode consists of two bytes: the lower byte must be pattern0, the upper byte must be pattern1
        self.ser.write("PATTERN_TIMING {p}\r".format(p = (pattern0) + (pattern1 << 8)).encode())
        resp = self.wait_for_OK() # something like: [b'PATTERN_TIMING 0xAA5\r\n5', b'TIMING: 23889736\r\n']
        cycles = int(resp[1].split()[1]) # second line, second word.
        if cycles == -1:
            return -1 # could not find patterns
        else:
            return cycles/48e6 # running at 48 MHz

    def transition_timing(self, pattern0, pattern1):
        self.ser.flushInput()
        # the opcode consists of two bytes: the lower byte must be pattern0, the upper byte must be pattern1
        self.ser.write("PATTERN_TRANSITION {p}\r".format(p = (pattern0) + (pattern1 << 8)).encode())
        resp = self.wait_for_OK() # something like: [b'PATTERN_TIMING 0xAA5\r\n5', b'TIMING: 23889736\r\n']
        cycles = int(resp[1].split()[1]) # second line, second word.
        if cycles == -1:
            return -1 # could not find patterns
        else:
            return cycles/48e6 # running at 48 MHz

    def write_dac(self, to_output):
        self.ser.flushInput()
        self.ser.write("DAC {val}".format(val = to_output).encode())
        self.wait_for_OK()
