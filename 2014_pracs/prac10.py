from interface_lib import InterrogatorInterface, OpenOCD
from gdb_lib import GDBInterface
import elf_parser
import shlex, subprocess
import time
import random
import os
import zipfile

class Prac10Tests:
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
        self.comment("Starting to run prac 10 tests")
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

                for test in [self.part1_tests, self.part2_tests, self.part3_tests, self.part4_tests, self.part5_tests]:
                    try:
                        mark += test()
                    except Exception as e:
                        self.comment("Unrecoverable exception while running test. Aborting")
                        self.comment(str(e))
                        self.comment(type(e))
                        break

                self.ii.highz_pin(0)
                self.ii.highz_pin(1)
                self.ii.highz_pin(2)
                self.ii.highz_pin(3)

        self.comment("All tests complete. Mark: {m}".format(m=mark))
        return mark

    def part1_tests(self):
        self.comment("=== Part 1 ===")
        self.comment("Verifying timing between all patterns. Should be 1 second +-6%.")
        pattern_array = [0x01, 0x02, 0x04, 0x08, 0x88, 0x48, 0x28, 0x18]
        for i in range(1, len(pattern_array)+3, 2):
            pat0 = pattern_array[i % len(pattern_array)]
            pat1 = pattern_array[(i+1) % len(pattern_array)]
            timing = round(self.ii.transition_timing(pat0, pat1), 3)
            self.comment("Timing between {p0:#x} and {p1:#x} found to be: {t}".format(p0 = pat0, p1 = pat1, t = timing))
            if timing < 1.0*0.88 or timing > 1*1.12:
                self.comment("Timing out. Awarding 0.")
                return 0
            elif timing < 1.0*0.94 or timing > 1*1.06:
                self.comment("Timing somewhat out. Awarding 1.")
                return 1
        self.comment("Correct. 2/2")
        return 2

    def part2_tests(self):
        mark = 1
        self.comment("=== Part 2 ===")
        self.comment("Waiting until pattern 0x48 is displayed.")
        t0 = time.time()
        leds = self.ii.read_port(0)
        while( (time.time() - t0 < 10.0) and leds != 0x48):
            leds = self.ii.read_port(0)
        if leds != 0x48:
            self.comment("Could not find 0x48 after 10 seconds. Timeout. 0/2")
            return 0
        self.comment("Pattern 0x48 is now on LEDs. Asserting a 100 ms pulse on SW0")
        self.ii.clear_pin(0)
        time.sleep(0.1)
        self.ii.highz_pin(0)
        time.sleep(0.1)
        pattern = self.ii.read_port(0)
        self.comment("Pattern should now be 0x01 and is {p:#x}.".format(p = pattern))
        if pattern != 0x01:
            self.comment("Incorrect. 0/2")
            return 0
        self.comment("Correct. 1/2")
        self.comment("Now holding SW0 down and ensuring that transitions occur.")
        self.ii.clear_pin(0)
        timing = round(self.ii.transition_timing(0x02, 0x04), 3)
        self.ii.highz_pin(0)
        if timing != -1:
            self.comment("Transition successfully found with SW0 held. 2/2")
            return 2
        self.comment("No transition found with SW0 held. 1/2")
        return 1

    def part3_tests(self):
        self.comment("=== Part 3 ===")
        self.comment("Pulsing SW0 again to reset pattern to start.")
        self.ii.clear_pin(0)
        time.sleep(0.1)
        self.ii.highz_pin(0)
        time.sleep(0.1)
        self.comment("Pulsing SW1 to change frequency to 2 Hz.")
        self.ii.clear_pin(1)
        time.sleep(0.1)
        self.ii.highz_pin(1)
        time.sleep(0.1)
        self.comment("Now looking for transition from 0x04 to 0x08. Should be 0.5 seconds +- 6%")
        timing = round(self.ii.transition_timing(0x04, 0x08), 3)
        self.comment("Timing found to be: {t}".format(t = timing))
        if timing < 0.5 * 0.9 or timing > 0.5 * 1.1:
            self.comment("Timing out. Awarding 0")
            return 0
        self.comment("Timing good. 2/2")
        return 2

    def part4_tests(self):
        self.comment("=== Part 4 ===")
        self.comment("Pulsing SW0 again to reset pattern to start.")
        self.ii.clear_pin(0)
        time.sleep(0.1)
        self.ii.highz_pin(0)
        time.sleep(0.1)
        self.comment("Pulsing SW2 to change frequency to 5 Hz.")
        self.ii.clear_pin(2)
        time.sleep(0.1)
        self.ii.highz_pin(2)
        time.sleep(0.1)
        self.comment("Now looking for transition from 0x04 to 0x08. Should be 0.2 seconds +- 6%")
        timing = round(self.ii.transition_timing(0x04, 0x08), 3)
        self.comment("Timing found to be: {t}".format(t = timing))
        if timing < 0.2 * 0.9 or timing > 0.2 * 1.1:
            self.comment("Timing out. Awarding 0")
            return 0
        self.comment("Timing good. Now checking that Part 3 tests still work.")
        if self.part3_tests() != 0:
            self.comment("Part 3 tests still good, awarding part 4. 1/1")
            return 1
        self.comment("Part 3 tests seem broken. Awarding 0")
        return 0


    def part5_tests(self):
        self.comment("=== Part 5 ===")
        self.comment("Asserting SW3.")
        self.ii.clear_pin(3)
        self.comment("Applying 0V to both pot0 and pot1. Frequency should be 1 Hz.")
        self.ii.write_dac(0)
        self.ii.configure_dac_channel(0, 0)
        self.ii.configure_dac_channel(1, 0)
        self.comment("Pulsing SW0 and looking for timing from 0x02 to 0x04.")
        self.ii.clear_pin(0)
        time.sleep(0.1)
        self.ii.highz_pin(0)
        time.sleep(0.1)
        timing = round(self.ii.transition_timing(0x02, 0x04), 3)
        self.comment("Timing found to be: {t}".format(t = timing))
        if timing < 1 * 0.9 or timing > 1 * 1.1:
            self.comment("Timing out. Awarding 0")
            return 0
        self.comment("Timing good.")
        self.ii.write_dac(50) # v = 50/256 * 3.3 = 0.645 V
        self.ii.configure_dac_channel(0, 1)
        self.ii.configure_dac_channel(1, 0)
        time.sleep(2)
        self.comment("Asserting 0.65 V on pot0 and 0 V on pot 1. Timing should be 0.814 seconds")
        self.comment("Pulsing SW0 and looking for timing from 0x02 to 0x04.")
        self.ii.clear_pin(0)
        time.sleep(0.1)
        self.ii.highz_pin(0)
        time.sleep(0.1)
        timing = round(self.ii.transition_timing(0x02, 0x04), 3)
        self.comment("Timing found to be: {t}".format(t = timing))
        if timing < 0.814 * 0.9 or timing > 0.814 * 1.1:
            self.comment("Timing out. Awarding 0")
            return 0
        self.comment("Timing good.")
        self.ii.write_dac(200) # v = 200/255 * 3.3 = 2.589 V
        self.ii.configure_dac_channel(0, 0)
        self.ii.configure_dac_channel(1, 1)
        time.sleep(2)
        self.comment("Asserting 2.589 V on pot1 and 0 V on pot 0. Timing should be 0.255 seconds")
        self.comment("Pulsing SW0 and looking for timing from 0x02 to 0x04.")
        self.ii.clear_pin(0)
        time.sleep(0.1)
        self.ii.highz_pin(0)
        time.sleep(0.1)
        timing = round(self.ii.transition_timing(0x02, 0x04), 3)
        self.comment("Timing found to be: {t}".format(t = timing))
        if timing < 0.255 * 0.9 or timing > 0.255 * 1.1:
            self.comment("Timing out. Awarding 0")
            return 0
        self.comment("All timing good. 3/3")
        return 3

