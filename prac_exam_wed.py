from interface_lib import InterrogatorInterface, OpenOCD
from gdb_lib import GDBInterface
import elf_parser
import shlex, subprocess
import time
import random
import os
import zipfile

class PracExamWedTests:
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
        self.comment("Starting to run *Wednesday* Prac Exam tests")
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

                self.ii.highz_pin(0)
                self.ii.highz_pin(1)
                self.ii.highz_pin(2)
                self.ii.highz_pin(3)
                self.ii.configure_dac_channel(0, 0)
                self.ii.configure_dac_channel(1, 0)
                
                time.sleep(0.5)

                for test in [self.part1_tests, self.part2_tests, self.part3_tests, self.part4_tests, self.part5_tests, self.part6_tests]:
                    try:
                        mark += test()
                    except Exception as e:
                        self.comment("Unrecoverable exception while running test. Aborting")
                        self.comment(str(e))
                        break

        self.comment("All tests complete. Mark: {m}".format(m=mark))
        return mark

    def part1_tests(self):
        self.comment("=== Part 1 ===")
        leds = self.ii.read_port(0)
        self.comment("After reset, LEDs should be 0xF0 and found to be: {l:#x}".format(l = leds))
        if leds == 0xF0:
            self.comment("Correct. 1/1")
            return 1
        self.comment("Incorrect")
        return 0

    def part2_tests(self):
        self.comment("=== Part 2 ===")
        self.comment("Asserting SW0")
        self.ii.clear_pin(0)
        self.comment("Applying voltage to POT0 such that the LEDS should be 0x40")
        self.ii.configure_dac_channel(0, 1)
        self.ii.write_dac(0x40)
        time.sleep(0.2)
        leds = self.ii.read_port(0)
        self.comment("LEDs found to read: {l:#x}".format(l = leds))
        if leds < 0x39 or leds > 0x47:
            self.comment("Too far out. 0/2")
            return 0
        self.comment("Okay. Next applying volatage such that LEDs should be 0xB7")
        self.ii.write_dac(0xB7)
        time.sleep(0.2)
        leds = self.ii.read_port(0)
        self.comment("LEDs found to read: {l:#x}".format(l = leds))
        if leds < 0xB0 or leds > 0xC0:
            self.comment("Too far out. 0/2")
            return 0
        self.comment("Passed. 2/2")
        return 2

    def part3_tests(self):
        self.comment("=== Part 3 ===")
        self.comment("Releasing SW0 and asserting SW1")
        self.ii.highz_pin(0)
        self.ii.clear_pin(1)
        self.comment("Applying Vmax to POT0. Timing should be 0.5 seconds.")
        self.ii.write_dac(0xFF)
        time.sleep(0.5)
        leds = self.ii.read_port(0)
        self.comment("LEDs currently showing {l:#x}. Looking for transistion from {l1:#x} to {l2:#x}".format(\
                l=leds, l1 = leds-2, l2 = leds-3))
        timing = round(self.ii.transition_timing(leds-2, leds-3), 3)
        self.comment("Transition timing found to be {t} seconds".format(t = timing))
        if timing < 0.5/1.12 or timing > 0.5*1.12:
            self.comment("Timing very out. 0/1")
            return 0
        if timing < 0.5/1.06 or timing > 0.5*1.06:
            self.comment("Timing somewhat out. 0.5/1")
            return 0.5
        self.comment("Timing correct. 1/1")
        return 1

    def part4_tests(self):
        self.comment("=== Part 4 ===")
        timing_somewhat_out = False
        self.comment("Keeping SW1 held. Now changing voltage.")
        self.comment("Asserting 0 V. Timing should be 0.125 s")
        self.ii.write_dac(0)
        time.sleep(0.5)
        leds = self.ii.read_port(0)
        self.comment("LEDs currently showing {l:#x}. Looking for transistion from {l1:#x} to {l2:#x}".format(\
                l=leds, l1 = leds-2, l2 = leds-3))
        timing = round(self.ii.transition_timing(leds-2, leds-3), 3)
        self.comment("Transition timing found to be {t} seconds".format(t = timing))
        if timing < 0.125/1.12 or timing > 0.125*1.12:
            self.comment("Timing very out. 0/2")
            return 0
        if timing < 0.125/1.06 or timing > 0.125*1.06:
            self.comment("Timing somewhat out.")
            timing_somewhat_out = True
        self.comment("Asserting voltage such that timing should be 0.39 s")
        self.ii.write_dac(180)
        time.sleep(0.5)
        leds = self.ii.read_port(0)
        self.comment("LEDs currently showing {l:#x}. Looking for transistion from {l1:#x} to {l2:#x}".format(\
                l=leds, l1 = leds-2, l2 = leds-3))
        timing = round(self.ii.transition_timing(leds-2, leds-3), 3)
        self.comment("Transition timing found to be {t} seconds".format(t = timing))
        if timing < 0.39/1.12 or timing > 0.39*1.12:
            self.comment("Timing very out. 0/2")
            return 0
        if timing < 0.39/1.06 or timing > 0.39*1.06:
            self.comment("Timing somewhat out.")
            timing_somewhat_out = True
        if  timing_somewhat_out == True:
            self.comment("Due to timing being somewhat out: 1/2")
            return 1
        self.comment("Timing good. 2/2")
        return 2


    def part5_tests(self):
        self.comment("=== Part 5 ===")
        mark = 2
        self.comment("Releasing SW1")
        self.ii.highz_pin(1)
        time.sleep(0.5)
        leds_pre = self.ii.read_port(0)
        self.comment("LEDs currently showing {l:#x}.".format(l=leds_pre))
        self.comment("Asserting a noisy falling edge on SW2")
        self.ii.clear_pin(2)  # about 2.5 ms between each transition.
        self.ii.highz_pin(2)
        self.ii.clear_pin(2)
        self.ii.highz_pin(2)
        self.ii.clear_pin(2)
        time.sleep(0.1)
        leds_post = self.ii.read_port(0)
        self.comment("LEDs now showing {l:#x}.".format(l=leds_post))
        if leds_post == leds_pre + 2:
            self.comment("Correctly dealt with falling edge")
        elif (leds_post <= leds_pre + 6) and (leds_post > leds_pre):
            self.comment("Debouncing not done correctly. At most 1/2")
            mark = 1
        else:
            self.comment("No change. Incorrect. 0/2")
            return 0
        self.comment("Asserting a noisy rising edge on SW2. Nothing should happen.")
        leds_pre = self.ii.read_port(0)
        self.ii.highz_pin(2)
        self.ii.clear_pin(2)
        self.ii.highz_pin(2)
        self.ii.clear_pin(2)
        self.ii.highz_pin(2)
        time.sleep(0.1)
        leds_post = self.ii.read_port(0)
        self.comment("LEDs now showing {l:#x}.".format(l=leds_post))
        if leds_post == leds_pre:
            self.comment("Correct. Mark: {m}".format(m = mark))
        else:
            self.comment("Rising edge did something. Bad.")
            mark -= 1
            self.comment("Mark: {m}".format(m = mark))
        return mark

    def part6_tests(self):
        self.comment("=== Part 6 ===")
        self.comment("Asserting SW3")
        self.ii.clear_pin(3)
        self.comment("Asserting 0 on POT0 and 0xB0 on POT1. Difference is 0xB0")
        self.ii.configure_dac_channel(0, 0)
        self.ii.configure_dac_channel(1, 1)
        self.ii.write_dac(0xB0)
        time.sleep(0.5)
        leds = self.ii.read_port(0)
        self.comment("LEDs showing: {l:#x}".format(l = leds))
        if leds > 0xB7 or leds < 0xA9:
            self.comment("Out. 0/2")
            return 0
        self.comment("Correct.")
        self.comment("Asserting 0x40 on POT0 and 0 on POT1. Difference is 0x40")
        self.ii.configure_dac_channel(0, 1)
        self.ii.configure_dac_channel(1, 0)
        self.ii.write_dac(0x40)
        time.sleep(0.5)
        leds = self.ii.read_port(0)
        self.comment("LEDs showing: {l:#x}".format(l = leds))
        if leds > 0x47 or leds < 0x39:
            self.comment("Out. 0/2")
            return 0
        self.comment("Correct. 2/2")
        return 2





