import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError, SourceFileProblem
import interrogator_interface
import gdb_interface

class Prac3Tests(PracTests):

    def catalogue_submission_files(self):
        os.chdir(self.submitter.submission_directory)
        all_files = os.listdir()
        self.logger.info("Directory contains: {f}".format(f = all_files))
        self.submitter.sfiles = [f for f in all_files if f.endswith(".s")]
        if len(self.submitter.sfiles) != 1:
            self.logger.critical("Too many or too few assembly files submitted")
            raise SourceFileProblem
        self.submitter.files_to_mark = \
            self.submitter.sfiles
        self.logger.info("Selected for marking: {f}".format(f = self.submitter.files_to_mark))
        self.submitter.files_for_plag_check = \
            self.submitter.sfiles

    def build(self):
        os.chdir(self.submitter.submission_directory)
        self.clean_marker_directory()
        os.chdir('/home/marker/')
        for f in self.submitter.files_to_mark:
            cmd = "cp \"{d}/{f}\" /home/marker/".format(d = self.submitter.submission_directory, f = f)
            self.exec_as_marker(cmd)
        self.logger.info("Running assembler in submission directory")
        try:
            self.exec_as_marker("arm-none-eabi-as -g -mthumb -mcpu=cortex-m0 -o main.o {s}".format(s = self.submitter.sfiles[0]))
        except BuildFailedError as e:
            self.logger.info("Received build error. Aborting")
            raise BuildFailedError
        self.logger.info("Running linker in submission directory")
        try:
            self.exec_as_marker("arm-none-eabi-ld -Ttext=0x08000000 -o main.elf main.o")
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
        self.gdb.open_file('main.elf')
        self.gdb.connect()
        self.gdb.erase()
        self.gdb.load()
        self.ii.highz_pin(0)
        self.ii.highz_pin(1)
        self.ii.highz_pin(2)
        self.ii.highz_pin(3)
        self.ii.write_dac(0, 0)
        try:
            self.logger.info("----------- PART 1 ----------------")
            self.part_1_tests()
            self.logger.info("----------- PART 2 ----------------")
            self.part_2_tests()
            self.logger.info("----------- PART 3 ----------------")
            self.part_3_tests()
            self.logger.info("----------- PART 4 ----------------")
            self.part_4_tests()
        except TestFailedError as e:
            self.logger.critical("A test failed. Marking cannot continue")
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
        except gdb_interface.GDBException as e:
            self.logger.critical("Your program did not respond the way GDB expected it to")


    def assert_led_value(self, val):
        leds = self.ii.read_port(0)
        self.logger.info("LEDs should read {v:#x}. Found to be: {l:#x}".format(v = val, l = leds))
        if leds == val:
            return True
        else:
            raise TestFailedError

    def part_1_tests(self):
        expected_values = [0x05, 0x14, 0x22, 0x31,
                        0x3A, 0x45, 0x5E, 0x62,
                        0x71, 0x7B, 0x8B, 0x99,
                        0xA4, 0xB0, 0xBD, 0xC9,
                        0xD8, 0xE7, 0xF2, 0xFE]
        self.gdb.run_to_label('stack_push_done')
        pointer = 0x20002000 - (4 * len(expected_values))
        for expected_value in expected_values:
            actual_value = self.gdb.read_word(pointer)
            self.logger.info("At address {addr:#x} expected {exp:#x} and found {act:#x}".format(
                addr = pointer,
                exp = expected_value,
                act = actual_value))
            if actual_value != expected_value:
                self.logger.critical("Incorrect.")
                raise TestFailedError
            pointer += 4
        self.submitter.increment_mark(2)
        self.logger.info("Changing address 0x20001FE0 to value 0x0000009A")
        self.gdb.write_word(0x20001FE0, 0x0000009A)
        self.logger.info("The closest pair should now be 0x99 and 0x9A")

    def part_2_tests(self):
        self.logger.info("So it seems I don't have a way to assess part2 directly... Oops")
        self.gdb.send_continue()

    def part_3_tests(self):
        self.logger.info("Checking timing for pattern transition: {p0:#X}->{p1:#X}".format(
            p0 = 0x99, p1 = 0x9A))
        try:
            timing = round(self.ii.timing_transition(0x99, 0x9A))
        except interrogator_interface.LEDTimingTimeout as e:
            p0 = self.ii.read_port(0)
            time.sleep(1)
            p1 = self.ii.read_port(1)
            self.logger.critical("LEDs did not seem to display expected pattern")
            self.logger.info("Rather, seemed to be displaying {p0:#X} and {p1:#X}".format(
                p0 = p0, p1 = p1))
            return
        self.logger.info("Found transition: part2 must be correct for a value not at the end of the stack.")
        self.submitter.increment_mark(1)
        self.logger.info("Now checking if it works if the best pair is the last pair")
        self.gdb.send_control_c()
        self.gdb.soft_reset()
        self.gdb.run_to_label('stack_push_done')
        self.logger.info("Changing address 0x20001FFC to value 0x000000F4")
        self.gdb.write_word(0x20001FFC, 0x000000F4)
        self.logger.info("The closest pair should now be 0xF2 and 0xF4")
        self.gdb.send_continue()
        time.sleep(2)
        try:
            timing = round(self.ii.timing_transition(0xF2, 0xF4))
            self.logger.info("Found pattern. Part 2 must be correct even for end of stack edge case")
            self.submitter.increment_mark(1)
        except interrogator_interface.LEDTimingTimeout as e:
            p0 = self.ii.read_port(0)
            time.sleep(1)
            p1 = self.ii.read_port(1)
            self.logger.critical("LEDs did not seem to display expected pattern")
            self.logger.info("Rather, seemed to be displaying {p0:#X} and {p1:#X}".format(
                p0 = p0, p1 = p1))
            self.logger.error("Not awarding full marks")
        self.gdb.send_control_c()
        self.gdb.soft_reset()
        self.gdb.send_continue()
        try:
            timing = round(self.ii.timing_transition(0x5E, 0x62))
        except interrogator_interface.LEDTimingTimeout as e:
            p0 = self.ii.read_port(0)
            time.sleep(1)
            p1 = self.ii.read_port(1)
            self.logger.critical("LEDs did not seem to display expected pattern")
            self.logger.info("Rather, seemed to be displaying {p0:#X} and {p1:#X}".format(
                p0 = p0, p1 = p1))
            self.logger.info("This should not be possible.....")
            return
        self.logger.info("Timing should be 1 second. Found to be {t} seconds.".format(t=timing))
        if (timing >= 0.95) and (timing <= 1.05):
            self.logger.info("Correct")
            self.submitter.increment_mark(1)
        else:
            self.logger.critical("Too far out. Exiting tests")
            raise TestFailedError

    def part_4_tests(self):
        self.gdb.send_control_c()
        self.gdb.soft_reset()
        self.gdb.send_continue()
        self.logger.info("Holding SW0")
        self.ii.clear_pin(0)
        time.sleep(2)
        self.ii.write_dac(0, 0)
        time.sleep(0.5)
        leds = self.ii.read_port(0)
        self.logger.info("Pot set to 0V, expecting 0 on LEDs")
        self.logger.info("LEDs found to display: {l:#x}".format(l = leds))
        if (leds > 5):
            self.logger.critical("Too far out")
            raise TestFailedError
        self.ii.write_dac(0, 0x30)
        time.sleep(0.5)
        leds = self.ii.read_port(0)
        self.logger.info("Pot set to 0.62V, expecting 0x30 on LEDs")
        self.logger.info("LEDs found to display: {l:#x}".format(l = leds))
        if (leds > 0x35) or (leds < 0x25):
            self.logger.critical("Too far out")
            raise TestFailedError
        self.ii.write_dac(0, 0xDD)
        time.sleep(0.5)
        leds = self.ii.read_port(0)
        self.logger.info("Pot set to 2.86V, expecting 0xDD on LEDs")
        self.logger.info("LEDs found to display: {l:#x}".format(l = leds))
        if (leds > 0xE4) or (leds < 0xD5):
            self.logger.critical("Too far out")
            raise TestFailedError
        self.submitter.increment_mark(2)
