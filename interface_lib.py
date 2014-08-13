import serial
import pexpect
import elf_parser
import re

class GDBInterface:
    def __init__(self, fi):
        self.fi = fi
        self.gdb = pexpect.spawn("arm-none-eabi-gdb", timeout=3)
        self.gdb.expect("\(gdb\)")
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        self.gdb.terminate(True)

    def open_file(self):
        self.gdb.sendline("file \"{}\"".format(self.fi))
        try:
            # we'll either get a done or a no such file
            if self.gdb.expect(["done.*\(gdb\)", "No such file or directory"]) == 0:
                return "file {} opened in GDB\r\n".format(fi)
            else:
                raise Exception("FATAL: Could not open file {} in GDB\r\n".format(fi))

    def connect(self):
        try:
            self.gdb.sendline("target remote localhost:3333")
            if self.gdb.expect(["Remote debugging using.*\(gdb\)", "Connection timed out"]) == 0:
                return "GDB connected to openOCD\r\n"
            else:
                raise Exception("FATAL: GDB could not connect to openOCD\r\n")

    def erase(self):
        gdb.sendline("monitor flash erase_sector 0 0 0")
        gdb.expect("erased sectors 0 through 0 on flash bank 0 in.*\(gdb\)")

    def load(self):
        gdb.sendline("load")
        gdb.expect("Transfer rate.*\(gdb\)")

    def run_to_label(self, label):
        address = elf_parser.get_address_of_label(self.fi, label)
        self.gdb.sendline("break *{}".format(address))
        self.gdb.expect("\(gdb\)")
        gdb.sendline("continue")
        gdb.expect("Breakpoint.*\(gdb\)")

    def read_word(self, address):
        gdb.sendline("x/1wx {}".format(address))
        gdb.expect("{}:".format(address))
        gdb.expect("\(gdb\)")
        return gdb.before.strip()
        
    def write_word(self, address, data):
        set_string = "set {{int}}{} = {}".format(address, data)
        self.gdb.sendline(set_string)
        self.gdb.expect(re.escape("{}\r\n(gdb)".format(set_string)))


class InterrogatorInterface:
    def __init__(self):
        self.ser = serial.Serial("/dev/ttyS0", 115200, timeout=2)

    def comms_test(self):
        self.ser.readlines()
        self.ser.write("PING 1\r")
        resp = self.ser.readlines()
        if resp[1] ==  b'PONG!\r\n':
            return "Communications with interrogator extablished\r\n"
        raise("No comms")

    def reset(self, state):
        self.ser.readlines()
        self.ser.write("NRST {}".format(state))
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


