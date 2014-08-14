import serial
import pexpect
import elf_parser
import re
import shlex, subprocess
import time
import logging

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
        self.gdb.expect("\(gdb\)")
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

    def erase(self):
        self.gdb.sendline("monitor flash erase_sector 0 0 0")
        self.gdb.expect("erased sectors 0 through 0 on flash bank 0 in.*\(gdb\)")
        self.comment("Microcontroller flash memory erased")

    def load(self):
        self.gdb.sendline("load")
        self.gdb.expect("Transfer rate.*\(gdb\)")
        self.comment(".elf file loaded into flash")

    def run_to_label(self, label):
        # improve this with custom exceptions!!!!
        try:
            address = elf_parser.get_address_of_label(self.fi, label) # this will throw an exception if label not found
        except:
            return False
        self.comment("Attempting to run to label {l} with address {a:#X}".format(l = label, a = address))
        self.comment("break *{a:#X}".format(a = address))
        self.gdb.sendline("break *{a:#x}".format(a = address))
        self.gdb.expect("\(gdb\)")
        self.gdb.sendline("continue")
        self.gdb.expect("Breakpoint.*\(gdb\)")
        self.comment("Hit breakpoint")
        return True

    def read_word(self, address):
        self.gdb.sendline("x/1wx {a:#x}".format(a = address))
        self.gdb.expect("{0:#x}:".format(address))
        self.gdb.expect("\(gdb\)")
        return int(self.gdb.before.strip(), 16)

    def write_word(self, address, data):
        set_string = "set {{int}}{a:#x} = {d:#x}".format(a = address, d = data)
        self.gdb.sendline(set_string)
        self.gdb.expect(re.escape("{}\r\n(gdb)".format(set_string)))
 

class InterrogatorInterface:
    def __init__(self):
        self.ser = serial.Serial("/dev/ttyS0", 115200, timeout=0.5)

    def comms_test(self):
        self.ser.flushInput()
        self.ser.write("PING 1\r".encode())
        resp = self.ser.readlines()
        if (len(resp) < 2) or (resp[1] ==  b'PONG!\r\n'):
            return "Communications with interrogator extablished"
        raise Exception("No comms with interrogator.")

    def reset(self, state):
        self.ser.flushInput()
        self.ser.write("NRST {}\r".format(state).encode())
        self.ser.readlines()

    def set_pin(pin):
        pass
    def clear_pin(pin):
        pass
    def write_port(port):
        pass
    def read_pin(pin):
        pass
    def read_port(port):
        pass


