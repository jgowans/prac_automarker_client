from interface_lib import InterrogatorInterface, OpenOCD
from gdb_lib import GDBInterface
import elf_parser
import shlex, subprocess
import time
import random
import os
import zipfile

class Prac9Tests:
    def __init__(self, comment, submission_dir, src_name):
        self.comment = comment
        self.src_name = src_name
        self.full_path_to_elf = None
        self.submission_dir = submission_dir

    def build(self):
        self.comment("Changing dir to submission dir")
        os.chdir(self.submission_dir)
        all_files = os.listdir()
        elf_files = [fi for fi in all_files if fi.endswith(".elf")]
        if len(elf_files) > 0:
            self.comment("Elf files exist before make run: {e}".format(e = all_files))
            self.comment("Aborting")
            return False
        self.comment("Running 'make'")
        make_proc = subprocess.Popen(["make"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            return_code = make_proc.wait(timeout = 5)
        except subprocess.TimeoutExpired:
            make_proc.kill()
            self.comment("Make did not complete after 5 seconds. Aborting")
            return False
        if (return_code != 0):
            error_message = make_proc.communicate()
            self.comment("Make failed. Awarding 0. Error message:")
            self.comment(error_message[0].decode())
            self.comment(error_message[1].decode())
            return False
        self.comment("Make succeeded. Attempting to link.")
        self.comment("Searching submission directory for .elf files")
        all_files = os.listdir()
        elf_files = [fi for fi in all_files if fi.endswith(".elf")]
        if len(elf_files) > 1:
            self.comment("Too many elf files out of {e}".format(e = all_files))
            return False
        if len(elf_files) == 0:
            self.comment("No elf files out of: {e}".format(e = all_files))
            return False
        self.comment("One elf file produced: {e}".format(e = elf_files[0]))
        self.full_path_to_elf = self.submission_dir + "/" + elf_files[0]
        return True

    def run_tests(self):
        mark = 0
        self.comment("Starting to run prac 9 tests")
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
                self.gdb.send_continue()

                for test in [self.part1_tests, self.part2_tests, self.part3_tests]:
                    try:
                        mark += test()
                    except Exception as e:
                        self.comment("Unrecoverable exception while running test. Aborting")
                        self.comment(str(e))
                        break

                if mark == 7:
                    mark += self.bonus_tests()
                else:
                    self.comment("Not attempting bonus due to previous errors")

                self.ii.highz_pin(0)
                self.ii.highz_pin(1)
                self.ii.highz_pin(2)
                self.ii.highz_pin(3)

        self.comment("All tests complete. Mark: {m}".format(m=mark))
        return mark

    def part1_tests(self):
        self.comment("=== Part 1 ===")
        self.comment("Releasing both SW2 and SW3")
        self.ii.highz_pin(2)
        self.ii.highz_pin(3)
        time.sleep(2)
        current_pattern = self.ii.read_port(0)
        timing = self.ii.transition_timing(current_pattern + 1, current_pattern + 2)
        self.comment("Timing between an increment expected to be 0.5 and found to be: {t}".format(t = round(timing, 2)))
        if timing < 0.46 or timing > 0.54:
            self.comment("Timing out. Awarding 0")
            return 0
        self.comment("Correct. 2/2")
        return 2

    def part2_tests(self):
        self.comment("=== Part 2 ===")
        self.comment("Releasing SW2 and pressing SW3")
        self.ii.highz_pin(2)
        self.ii.clear_pin(3)
        time.sleep(0.6)
        current_pattern = self.ii.read_port(0)
        timing = self.ii.transition_timing(current_pattern - 1, current_pattern - 2)
        self.comment("Timing between a decrement expected to be 0.5 and found to be: {t}".format(t = round(timing, 2)))
        if timing < 0.47 or timing > 0.53:
            self.comment("Timing out. Awarding 0")
            return 0
        self.comment("Correct. 1/1")
        self.ii.highz_pin(2)
        self.ii.highz_pin(3)
        return 2

    def part3_tests(self):
        self.comment("=== Part 3 ===")
        self.comment("Pressing SW2 and releasing SW3")
        self.ii.clear_pin(2)
        self.ii.highz_pin(3)
        self.comment("Asserting 0.52 V on port A6. Period should become 0.16 seconds.")
        self.ii.write_dac(40)
        time.sleep(1)
        current_pattern = self.ii.read_port(0)
        timing = self.ii.transition_timing(current_pattern + 1, current_pattern + 2)
        self.comment("Timing between an increment found to be: {t}".format(t = round(timing, 2)))
        if timing < 0.14 or timing > 0.18:
            self.comment("Timing out. Awarding 0")
            return 0
        self.comment("Pressing SW2 and pressing SW3")
        self.ii.clear_pin(2)
        self.ii.clear_pin(3)
        self.comment("Asserting 1.93 V on port A6. Period should become 0.33 seconds.")
        self.ii.write_dac(150)
        time.sleep(1)
        current_pattern = self.ii.read_port(0)
        timing = self.ii.transition_timing(current_pattern - 1, current_pattern - 2)
        self.comment("Timing between an decrement found to be: {t}".format(t = round(timing, 2)))
        if timing < 0.30 or timing > 0.36:
            self.comment("Timing out. Awarding 0")
            return 0
        return 3


    def bonus_tests(self):
        self.comment("=== Bonus ===")
        self.comment("Releasing SW2 and SW3.")
        self.ii.highz_pin(2)
        self.ii.highz_pin(3)
        time.sleep(1)
        value_before_rst = self.ii.read_port(0)
        self.ii.reset(0)
        self.comment("Value on LEDs before reset: {leds:#x}".format(leds = value_before_rst))
        self.comment("Pulling NRST line low and sleeping for 2 seconds.")
        time.sleep(2)
        self.comment("Releasing NSRT line and sleeping for 100 ms")
        self.ii.reset(1)
        time.sleep(0.1)
        value_after_rst = self.ii.read_port(0)
        self.comment("Value on LEDs after reset: {leds:#x}".format(leds = value_after_rst))
        if value_before_rst != value_after_rst:
            self.comment("Values different. 0/0")
            return 0
        self.comment("Bonus correct! 1/0")
        return 1

