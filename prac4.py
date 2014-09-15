import serial
from interface_lib import InterrogatorInterface, GDBInterface, OpenOCD
import shlex, subprocess
import time
import random

data_array = [0x22F65244, 0x4E66ECA3, 0x25C1C308, 0xE278D1CA, 0x10E865FE, 0x839B17FB, 0xDE6AC773, 0x49A0392B, 0x0442B580, 0xAE6E269D, 0xCB220366, 0x603DEBBE, 0xFD88B1BF, 0x49C5652F, 0x25476C5A, 0xA5C40771, 0xB04D908D, 0x831C1806, 0x5B4F75D4, 0x6B016B93, 0x90DCB11A, 0xEFB6E394, 0x44DB27DA, 0xCF205F79, 0xB1192A24, 0x79CF44E2, 0x371CE3BA, 0x7A279FF5, 0x006047DC, 0xFA165142, 0x12690FDC, 0x5AAD829E, 0x19244BA0, 0x0B5174A3, 0xBD7172C8, 0x1D3B229F, 0xADA0357E, 0x1D44E4E6, 0x37CAA86E, 0x6A08FC5D, 0x465FAEE1, 0x2E52E372, 0xD6016409, 0x52012177, 0x848249E0, 0xCEE8EC8D, 0xCA09FBE7, 0x45EC4E32, 0xA11CCFB5, 0x95584228]

class Prac4Tests:
    def __init__(self, comment, submission_dir, src_name):
        self.comment = comment
        self.src_name = src_name
        self.full_path_to_elf = None
        self.submission_dir = submission_dir

    def build(self):
        print("building {f} in dir: {d}".format(f= self.src_name, d=self.submission_dir))
        as_proc = subprocess.Popen(["arm-none-eabi-as", \
                "-mcpu=cortex-m0", "-mthumb", "-g", \
                "-o", self.submission_dir + "/main.o", \
                self.submission_dir + "/" + self.src_name], \
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if (as_proc.wait() != 0):
            error_message = as_proc.communicate()
            self.comment("Compile failed. Awarding 0. Error message:")
            self.comment(error_message[0].decode())
            self.comment(error_message[1].decode())
            return False
        self.comment("Compile succeeded. Attempting to link.")
        ld_proc = subprocess.Popen(["arm-none-eabi-ld", \
                "-Ttext=0x08000000", \
                "-o", self.submission_dir + "/main.elf", \
                self.submission_dir + "/main.o"], \
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if (ld_proc.wait() != 0):
            error_message = ld_proc.communicate()
            self.comment("Link failed. Awarding 0. Error message:")
            self.comment(error_message[0].decode())
            self.comment(error_message[1].decode())
            return False
        self.full_path_to_elf = self.submission_dir + "/main.elf"
        self.comment("Link succeeded")
        return True

    def run_tests(self):
        mark = 0
        self.comment("Starting to run prac 4 tests")
        self.ii = InterrogatorInterface()
        self.comment(self.ii.comms_test())
        self.ii.reset(0) # pull line low. This does a reset
        with OpenOCD(self.comment) as self.openocd:
            time.sleep(0.2)
            self.ii.reset(1) # release line. Allows OpenOCD to establish connection to core.
            with GDBInterface(self.full_path_to_elf, self.comment) as self.gdb:
                self.gdb.open_file()
                self.gdb.connect()
                self.gdb.erase()
                self.gdb.load()
                self.comment("=== Part 1 ===")
                mark += self.part1_tests()

                self.comment("===Part 2 ===")
                mark += self.part2_tests()

                self.comment("Sending 'continue' to allow code to free-run")
                self.gdb.send_continue()
                
                self.comment("=== Part 3 ===")
                mark += self.part3_tests()

                self.comment("=== Part 4 ===")
                mark += self.part4_tests()

                self.comment("=== Part 5 ===")
                mark += self.part5_tests()

                self.ii.highz_pin(0)
                self.ii.highz_pin(1)

        self.comment("All tests complete. Mark: {m}".format(m=mark))
        return mark

    def part1_tests(self):
        if self.gdb.run_to_label("copy_to_RAM_complete") == False:
            self.comment("Could not hit label 'copy_to_RAM_complete'. Aborting")
            return 0
        self.comment("Verifying array in RAM")
        for idx, val in enumerate(data_array):
            address = 0x20000000 + (4*idx)
            data_in_RAM = self.gdb.read_word(address)
            if data_in_RAM != val:
                self.comment("Data at address {addr:#x} should be {v:#x} but is {d:#x}".format(addr = address, v = val, d = data_in_RAM))
                return 0
        self.comment("Data correct in RAM. 3/3")
        return 3

    def part2_tests(self):
        if self.gdb.run_to_label("increment_of_bytes_complete") == False:
            self.comment("Could not hit label 'increment_of_bytes_complete'. Aborting")
            return 0
        self.comment("Verifying incremented array in RAM")
        mark_to_return = 2
        for idx, val in enumerate(data_array):
            address = 0x20000000 + (4*idx)
            data_in_RAM = self.gdb.read_word(address)
            for byte_offset in range(0, 3):
                # add one at the correct place, then shift the byte of interest down to LSB and select with mask
                val_byte = ((val + (1 << (byte_offset * 8))) >> (byte_offset * 8)) & 0xFF
                data_byte = ((data_in_RAM ) >> (byte_offset * 8)) & 0xFF
            if val_byte != data_byte:
                self.comment("Data at address {addr:#x} should be {v:#x} but is {d:#x}".format( \
                        addr = address + byte_offset, v = val_byte, d = data_byte))
                self.comment("Aborting verification phase. 0/2")
                mark_to_return = 0
                break
        if mark_to_return == 2:
            self.comment("Data correct in RAM. 2/2")
        self.comment("Now modifying data in RAM. Setting all words to 0x88888888")
        for word_offset in range(0, len(data_array)):
            word_addr = 0x20000000 + (word_offset*4)
            self.gdb.write_word(word_addr, 0x88888888)
        self.comment("Setting address 0x2000000C0 to 0x8870FA05")
        self.comment("This implies a max unsigned of 0xFA, min unsigned of 0x05 and max signed of 0x70")
        self.gdb.write_word(0x20000008, 0x8870FA05)
        return mark_to_return

    def part3_tests(self):
        # simulate SW1 and not SW0. Should be flashing AA,55 at 0.25 seconds
        self.ii.highz_pin(0)
        self.ii.highz_pin(1)
        time.sleep(0.5)
        self.comment("Releasing both SW0 and SW1")
        led_data = self.ii.read_port(0)
        self.comment("Data on LEDs should be max unsigned (0xFA), and found to be {d:#X}".format(d=led_data))
        if led_data != 0xFA:
            self.comment("Incorrect. 0/3")
            return 0
        self.comment("Part 3 correct. 3/3")
        return 3

    def part4_tests(self):
        # simulate SW1 and not SW0. Should be flashing AA,55 at 0.25 seconds
        self.ii.clear_pin(0)
        self.ii.highz_pin(1)
        time.sleep(0.5)
        self.comment("Pressing SW0 and releasing SW1")
        led_data = self.ii.read_port(0)
        self.comment("Data on LEDs should be min unsigned (0x05), and found to be {d:#X}".format(d=led_data))
        if led_data != 0x05:
            self.comment("Incorrect. 0/2")
            return 0
        self.comment("Part 4 correct. 2/2")
        return 2

    def part5_tests(self):
        # simulate SW1 and not SW0. Should be flashing AA,55 at 0.25 seconds
        self.ii.highz_pin(0)
        self.ii.clear_pin(1)
        time.sleep(0.5)
        self.comment("Releasing SW0 and pressing SW1")
        led_data = self.ii.read_port(0)
        self.comment("Data on LEDs should be max signed (0x70), and found to be {d:#X}".format(d=led_data))
        if led_data != 0x70:
            self.comment("Incorrect. 0/1")
            return 0
        self.comment("Part 5 correct. 1/1")
        return 1
