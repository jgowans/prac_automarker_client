import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError
import interrogator_interface
import gdb_interface

class Prac4Tests(PracTests):
    def build(self):
        self.clean_marker_directory()
        os.chdir('/home/marker/')
        for f in self.group.files:
            cmd = "cp \"{d}/{f}\" /home/marker/".format(d = self.group.submission_directory, f = f)
            self.exec_as_marker(cmd)
        all_files = os.listdir()
        s_files = [fi for fi in all_files if fi.endswith(".s")]
        if len(s_files) != 1:
            self.logger.critical("Too many or too few .s files found. Should be only 1 .s file. Actual directory contents: {af}".format(af = all_files))
            raise BuildFailedError
        self.logger.info("Found only 1 .s file. Good!")
        cmd = "sed -i \"s/.word 0xfbe4bc46/.word 0x0674a70b\\n .word 0x0674a70b\\n .word 0x55AA55AA\\n .word 0xFD0155AA\\n/g\" {f}".format(f = s_files[0])
        self.exec_as_marker(cmd)
        self.logger.info("Your source file has been modified to replace .word 0xfbe4bc46 with .word 0x0674a70b .word 0x0674a70b .word 0x55AA55AA 0xFD0155AA")
        self.logger.info("The DATA block is a tad longer and now the best pair should be 0xFD and 0x01")
        self.logger.info("Running 'make' in submission directory")
        try:
            self.exec_as_marker("timeout 5 make")
        except BuildFailedError as e:
            self.logger.info("Received build error. Aborting")
            raise BuildFailedError
        all_files = os.listdir()
        elf_files = [fi for fi in all_files if fi.endswith(".elf")]
        if len(elf_files) != 1:
            self.logger.critical("Too few or too many elf files found after make. Directory contents: {af}".format(af = all_files))
            raise BuildFailedError
        self.elf_file = elf_files[0]

    def run_specific_prac_tests(self):
        self.gdb.open_file(self.elf_file)
        self.gdb.connect()
        self.gdb.erase()
        self.gdb.load()
        self.ii.highz_pin(0)
        self.ii.highz_pin(1)
        self.ii.highz_pin(2)
        self.ii.highz_pin(3)
        self.ii.write_dac(0, 0)
        self.ii.write_dac(1, 0)
        try:
            self.logger.info("----------- PART 1 ----------------")
            self.part_1_tests()
            self.logger.info("----------- PART 2 ----------------")
            self.part_2_tests()
            self.logger.info("----------- PART 3 ----------------")
            self.part_3_tests()
            self.logger.info("----------- PART 4 ----------------")
            self.part_4_tests()
            self.logger.info("----------- PART 5 ----------------")
            self.part_5_tests()
        except TestFailedError as e:
            self.logger.critical("A test failed. Marking cannot continue")
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
        except gdb_interface.GDBException as e:
            self.logger.critical("Your program did not respond the way GDB expected it to")
        finally:
            self.logger.info("---- Checking submission time ----")
            self.adjust_mark()


    def assert_led_value(self, val):
        leds = self.ii.read_port(0)
        self.logger.info("LEDs should read {v:#x}. Found to be: {l:#x}".format(v = val, l = leds))
        if leds == val:
            return True
        else:
            raise TestFailedError

    def part_1_tests(self):
        self.logger.info("Wiping RAM")
        for address in range(0x20000000, 0x20000000+(20*4), 4):
            self.gdb.write_word(address, 0)
        for address in range(0x20001FE0, 0x20002000+(20*4), 4):
            self.gdb.write_word(address, 0)
        expected_values = [0x62967109,
                           0x0674a70b,
                           0x902bff4f,
                           0xe7fa8a65,
                           0xb610c2fe,
                           0x237e8814,
                           0xfe0573a4,
                           0xefd6e381,
                           0x33c8bf70,
                           0x0674a70b,
                           0x0674a70b,
                           0x55AA55AA,
                           0xFD0155AA]
        self.gdb.run_to_label('copy_to_RAM_done')
        pointer = 0x20000000
        for expected_value in expected_values:
            actual_value = self.gdb.read_word(pointer)
            self.logger.info("At address {addr:#x} expected {exp:#x} and found {act:#x}".format(
                addr = pointer,
                exp = expected_value,
                act = actual_value))
            if actual_value != expected_value:
                self.logger.critical("Incorrect.")
                return
            pointer += 4
        self.group.increment_mark(1)

    def part_2_tests(self):
        self.part_2_incorrect = False
        self.part_2_top = 0x01
        self.part_2_second = 0xFD
        self.gdb.run_to_label('closest_pair_finding_done')
        sp = self.gdb.get_variable_value("$sp")
        self.logger.info("SP found to hold the value: {sp:#x}".format(sp = sp))
        self.logger.info("Expecting the larger of the elements (B) of value 0x01 to be on the top of the stack")
        top = self.gdb.read_word(sp)
        self.logger.info("At address {sp:#x} found: {v:#x}".format(sp = sp, v = top))
        if top != 0x01:
            self.logger.critical("Incorrect. A note has been made to rather look for the pattern your code has found")
            self.part_2_incorrect = True
            self.part_2_top = (top & 0xFF)
        second = self.gdb.read_word(sp+4)
        self.logger.info("Expecting the smaller element (A) of value 0xFFFFFFFD (or 0xFD) to be second from top")
        self.logger.info("At address {sp:#x} found: {v:#x}".format(sp = sp+4, v = second))
        if (second != 0xFFFFFFFD) and (second != 0xFD):
            self.logger.critical("Incorrect. A note has been made to rather look for the pattern your code has found")
            self.part_2_second = (second & 0xFF)
            self.part_2_incorrect = True
        if self.part_2_incorrect == True:
            if (self.part_2_top == 0xFFFFFFFD or self.part_2_top == 0xFD) and (self.part_2_second == 0x01):
                self.logger.info("It seems you only got the order the wrong way around. Awarding 1/2")
                self.group.increment_mark(1)
            else:
                self.logger.info("Not awarding marks for part 2, but still attempitng to mark the rest. This may or may not work....")
        else:
            self.logger.info("Correct!")
            self.group.increment_mark(2)

    def part_3_tests(self):
        self.gdb.send_continue()
        if self.part_2_incorrect == True:
            self.logger.info("Attempting to find either the transition: {p0:#x}->{p1:#x} or {p2:#x}->{p3:#x}".format(
                p0 = 0x01, p1 = 0xFD, p2 = self.part_2_top, p3 = self.part_2_second))
            try:
                timing = round(self.ii.timing_transition(0xFD, 0x01), 2)
                self.part_2_top = 0xFD
                self.part_2_second = 0x01
            except interrogator_interface.LEDTimingTimeout as e:
                try:
                    timing = round(self.ii.timing_transition(self.part_2_top, self.part_2_second), 2)
                except interrogator_interface.LEDTimingTimeout as e:
                    p0 = self.ii.read_port(0)
                    time.sleep(1.5)
                    p1 = self.ii.read_port(1)
                    self.logger.critical("Could not find either patterns.")
                    self.logger.info("Rather, seemed to be displaying {p0:#X} and {p1:#X}".format(
                        p0 = p0, p1 = p1))
                    return
        else:
            self.logger.info("Checking timing for pattern transition: {p0:#X}->{p1:#X}".format(
                p0 = 0xFD, p1 = 0x01))
            try:
                timing = round(self.ii.timing_transition(0xFD, 0x01), 2)
                self.part_2_top = 0xFD
                self.part_2_second = 0x01
            except interrogator_interface.LEDTimingTimeout as e:
                p0 = self.ii.read_port(0)
                time.sleep(1.5)
                p1 = self.ii.read_port(1)
                self.logger.critical("LEDs did not seem to display expected pattern")
                self.logger.info("Rather, seemed to be displaying {p0:#X} and {p1:#X}".format(
                    p0 = p0, p1 = p1))
                return
        self.logger.info("Timing should be 1.5 seconds. Found to be {t} seconds.".format(t=timing))
        if (timing >= 1.5*0.95) and (timing <= 1.5*1.05):
            self.logger.info("Correct")
            self.group.increment_mark(1)
        else:
            self.logger.critical("Too far out. Exiting tests")
            raise TestFailedError

    def part_4_tests(self):
        self.logger.info("Holding SW0")
        self.ii.clear_pin(0)
        self.logger.info("Setting POT0 to 0xD0 and POT1 to 0")
        self.ii.write_dac(0, 0xD0)
        time.sleep(2)
        self.logger.info("Timing should be 0.85 seconds")
        try:
            timing = round(self.ii.timing_transition(self.part_2_top, self.part_2_second), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            p0 = self.ii.read_port(0)
            time.sleep(0.85)
            p1 = self.ii.read_port(1)
            self.logger.critical("LEDs did not seem to display expected pattern")
            self.logger.info("Rather, seemed to be displaying {p0:#X} and {p1:#X}".format(
                p0 = p0, p1 = p1))
            return
        self.logger.info("Found to be {t} seconds.".format(t=timing))
        if (timing >= 0.85*0.95) and (timing <= 0.85*1.05):
            self.logger.info("Correct")
        else:
            self.logger.critical("Too far out.")
            return

        self.logger.info("Setting POT0 to 0x40 and POT1 to 0")
        self.ii.write_dac(0, 0x55)
        time.sleep(2)
        self.logger.info("Timing should be 0.47 seconds")
        try:
            timing = round(self.ii.timing_transition(self.part_2_top, self.part_2_second), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            p0 = self.ii.read_port(0)
            time.sleep(0.47)
            p1 = self.ii.read_port(1)
            self.logger.critical("LEDs did not seem to display expected pattern")
            self.logger.info("Rather, seemed to be displaying {p0:#X} and {p1:#X}".format(
                p0 = p0, p1 = p1))
            return
        self.logger.info("Found to be {t} seconds.".format(t=timing))
        if (timing >= 0.47*0.95) and (timing <= 0.47*1.05):
            self.logger.info("Correct")
        else:
            self.logger.critical("Too far out.")
            return
        self.group.increment_mark(2)

    def part_5_tests(self):
        self.logger.info("Setting POT0 to 0x30 and POT1 to 0x60")
        self.ii.write_dac(0, 0x30)
        self.ii.write_dac(1, 0x60)
        time.sleep(2)
        self.logger.info("Timing should be 0.5 seconds")
        try:
            timing = round(self.ii.timing_transition(self.part_2_top, self.part_2_second), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            p0 = self.ii.read_port(0)
            time.sleep(0.5)
            p1 = self.ii.read_port(1)
            self.logger.critical("LEDs did not seem to display expected pattern")
            self.logger.info("Rather, seemed to be displaying {p0:#X} and {p1:#X}".format(
                p0 = p0, p1 = p1))
            return
        self.logger.info("Found to be {t} seconds.".format(t=timing))
        if (timing >= 0.5*0.95) and (timing <= 0.5*1.05):
            self.logger.info("Correct")
        else:
            self.logger.critical("Too far out.")
            return

        self.logger.info("Setting POT0 to 0x00 and POT1 to 0x0")
        self.ii.write_dac(0, 0)
        self.ii.write_dac(1, 0)
        time.sleep(2)
        self.logger.info("Timing should be 0.2 seconds")
        try:
            timing = round(self.ii.timing_transition(self.part_2_top, self.part_2_second), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            p0 = self.ii.read_port(0)
            time.sleep(0.2)
            p1 = self.ii.read_port(1)
            self.logger.critical("LEDs did not seem to display expected pattern")
            self.logger.info("Rather, seemed to be displaying {p0:#X} and {p1:#X}".format(
                p0 = p0, p1 = p1))
            return
        self.logger.info("Found to be {t} seconds.".format(t=timing))
        if (timing >= 0.2*0.95) and (timing <= 0.2*1.05):
            self.logger.info("Correct")
        else:
            self.logger.critical("Too far out.")
            return

        self.logger.info("Setting POT0 to 0xF0 and POT1 to 0xE0")
        self.ii.write_dac(0, 0xF0)
        self.ii.write_dac(1, 0xE0)
        time.sleep(2)
        self.logger.info("Timing should be 0.95 seconds")
        try:
            timing = round(self.ii.timing_transition(self.part_2_top, self.part_2_second), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            p0 = self.ii.read_port(0)
            time.sleep(0.95)
            p1 = self.ii.read_port(1)
            self.logger.critical("LEDs did not seem to display expected pattern")
            self.logger.info("Rather, seemed to be displaying {p0:#X} and {p1:#X}".format(
                p0 = p0, p1 = p1))
            return
        self.logger.info("Found to be {t} seconds.".format(t=timing))
        if (timing >= 0.95*0.95) and (timing <= 0.95*1.05):
            self.logger.info("Correct")
        else:
            self.logger.critical("Too far out.")
            return

        self.group.increment_mark(2)

    def adjust_mark(self):
        if self.group.submission_time < time.strptime("27 August 2015 09:55", "%d %B %Y %H:%M"):
            self.logger.info("Submitted on time - no adjustment")
        else:
            self.logger.info("Submitted after Thursday, 1 mark adjutment")
            self.group.increment_mark(-1)
            self.group.mark = max(self.group.mark, 0)
