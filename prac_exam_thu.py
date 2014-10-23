from interface_lib import InterrogatorInterface, OpenOCD
from gdb_lib import GDBInterface
import elf_parser
import shlex, subprocess
import time
import random
import os
import zipfile

pattern_array = [0x03, 0x06, 0x0C, 0x18, 0x30, 0x60, 0xC0, 0x00]

class PracExamThuTests:
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
        self.comment("Starting to run *Thursday* Prac Exam tests")
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

                for test in [self.part1_tests, self.part2_tests, self.part3_tests, self.part4_tests, self.part5_tests]:
                    try:
                        mark += test()
                    except Exception as e:
                        self.comment("Unrecoverable exception while running test. Aborting")
                        self.comment(str(e))
                        self.comment(type(e))
                        break

        self.comment("All tests complete. Mark: {m}".format(m=mark))
        return mark

    def part1_tests(self):
        self.comment("=== Part 1 ===")
        self.comment("Applying Vmax to POT0. Timing should be 0.5 seconds.")
        self.ii.configure_dac_channel(0, 1)
        self.ii.configure_dac_channel(1, 0)
        self.ii.write_dac(0xFF)
        time.sleep(0.5)
        timing_marginal = False
        self.comment("Holding SW0 and looking for pattern timings")
        self.ii.clear_pin(0)
        time.sleep(0.1)
        for i in range(2, len(pattern_array)+3, 2):
            pat0 = pattern_array[i % len(pattern_array)]
            pat1 = pattern_array[(i+1) % len(pattern_array)]
            timing = round(self.ii.transition_timing(pat0, pat1), 3)
            self.comment("Timing between {p0:#x} and {p1:#x} found to be: {t}".format(p0 = pat0, p1 = pat1, t = timing))
            if timing < 0.5*0.88 or timing > 0.5*1.12:
                self.comment("Timing out. Awarding 0.")
                return 0
            elif timing < 0.5*0.94 or timing > 0.5*1.06:
                self.comment("Timing further out than it should be. At most 1/2.")
                timing_marginal = True
        if timing_marginal == True:
            self.comment("Mark = 1/2")
            return 1
        self.comment("Mark = 2/2")
        return 2

    def part2_tests(self):
        mark = 2
        self.comment("=== Part 2 ===")
        self.comment("Releasing SW0")
        self.ii.highz_pin(0)
        time.sleep(0.5)
        leds = self.ii.read_port(0)
        self.comment("LEDs found to be {l:#x}".format(l = leds))
        try:
            idx = pattern_array.index(leds)
        except:
            self.comment("This pattern is part of the array. Aborting.")
            return 0
        self.comment("This is array index: {i}".format(i = idx))
        self.comment("Asserting a noisy falling edge on SW1")
        self.ii.clear_pin(1)  # about 2.5 ms between each transition.
        self.ii.highz_pin(1)
        self.ii.clear_pin(1)
        self.ii.highz_pin(1)
        self.ii.clear_pin(1)
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.comment("LEDs found to be {l:#x}".format(l = leds))
        try:
            idx_new = pattern_array.index(leds)
        except:
            self.comment("This pattern is part of the array. Aborting.")
            return 0
        self.comment("This is array index: {i}".format(i = idx))
        if (idx_new < idx):
            diff = len(pattern_array) + idx_new - idx
        else:
            diff = idx_new - idx
        self.comment("This is a difference of: {d}".format(d = diff))
        if diff == 0:
            self.comment("No change. 0/2")
            return 0
        elif diff == 1:
            self.comment("Correct.")
        elif diff < 4:
            self.comment("Too much change. At most 1/2")
            mark -= 1
        else:
            self.comment("Too much change. 0/2")
            return 0
        idx = idx_new
        self.comment("Asserting a noisy rising edge on SW1. Nothing should happen.")
        self.ii.highz_pin(1)
        self.ii.clear_pin(1)
        self.ii.highz_pin(1)
        self.ii.clear_pin(1)
        self.ii.highz_pin(1)
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.comment("LEDs found to be {l:#x}".format(l = leds))
        try:
            idx_new = pattern_array.index(leds)
        except:
            self.comment("This pattern is part of the array. Aborting.")
            return 0
        self.comment("This is array index: {i}".format(i = idx))
        if (idx_new < idx):
            diff = len(pattern_array) + idx_new - idx
        else:
            diff = idx_new - idx
        self.comment("This is a difference of: {d}".format(d = diff))
        if diff == 0:
            self.comment("Correct. Mark = {m}/2".format(m = mark))
        else:
            mark -= 1
            self.comment("Something happened on the rising edge. Bad. Mark = {m}/2".format(m = mark))
        return mark

    def part3_tests(self):
        self.comment("=== Part 3 ===")
        self.ii.highz_pin(1)
        time.sleep(0.5)
        timing_marginal = False
        self.comment("Holding SW2 and looking for pattern timings running BACKWARDS")
        self.ii.clear_pin(2)
        time.sleep(0.1)
        for i in range(len(pattern_array)+3, 0, -2):
            pat0 = pattern_array[i % len(pattern_array)]
            pat1 = pattern_array[(i-1) % len(pattern_array)]
            timing = round(self.ii.transition_timing(pat0, pat1), 3)
            self.comment("Timing between {p0:#x} and {p1:#x} found to be: {t}".format(p0 = pat0, p1 = pat1, t = timing))
            if timing < 0.5*0.88 or timing > 0.5*1.12:
                self.comment("Timing out. Awarding 0.")
                return 0
            elif timing < 0.5*0.94 or timing > 0.5*1.06:
                self.comment("Timing further out than it should be. At most 0.5/1.")
                timing_marginal = True
        if timing_marginal == True:
            self.comment("Mark = 0.5/1")
            return 0.5
        self.comment("Mark = 1/1")
        return 1

    def part4_tests(self):
        self.comment("=== Part 4 ===")
        self.comment("Asserting 0 V on POT0. Timing should be 0.05 seconds")
        self.ii.configure_dac_channel(0, 0)
        self.ii.configure_dac_channel(1, 0)
        self.ii.write_dac(0)
        timing_somewhat_out = False
        self.comment("Asserting SW0 and releasing SW2- expecting patterns to go forward")
        self.ii.highz_pin(2)
        self.ii.clear_pin(0)
        time.sleep(0.5)
        self.comment("Timing transition from 0x18 to 0x30")
        timing = round(self.ii.transition_timing(0x18, 0x30), 3)
        self.comment("Transition timing found to be {t} seconds".format(t = timing))
        if timing < 0.05/1.16 or timing > 0.05*1.16:
            self.comment("Timing very out. 0/2")
            return 0
        if timing < 0.05/1.08 or timing > 0.05*1.08:
            self.comment("Timing somewhat out.")
            timing_somewhat_out = True
        self.comment("Releasing SW0 and asserting SW2. Patterns should go backwards")
        self.ii.highz_pin(0)
        self.ii.clear_pin(2)
        time.sleep(0.5)
        self.comment("Asserting voltage 3.3*200/255 such that timing should be 0.4 s")
        self.ii.configure_dac_channel(0, 1)
        self.ii.write_dac(200)
        time.sleep(0.5)
        self.comment("Timing transition from 0x0C to 0x06")
        timing = round(self.ii.transition_timing(0x0C, 0x06), 3)
        self.comment("Transition timing found to be {t} seconds".format(t = timing))
        if timing < 0.4/1.12 or timing > 0.4*1.12:
            self.comment("Timing very out. 0/2")
            return 0
        if timing < 0.4/1.06 or timing > 0.4*1.06:
            self.comment("Timing somewhat out.")
            timing_somewhat_out = True
        if  timing_somewhat_out == True:
            self.comment("Due to timing being somewhat out: 1/2")
            return 1
        self.comment("Timing good. 2/2")
        return 2


    def part5_tests(self):
        self.comment("=== Part 5 ===")
        timing_marginal = False
        self.comment("Releasing SW0 and SW2, while asserting SW3")
        self.ii.highz_pin(0)
        self.ii.highz_pin(2)
        self.ii.clear_pin(3)
        self.comment("Asserting Vmax on POT1. LEDs should be flashing between 0 and FF")
        self.ii.configure_dac_channel(0, 0)
        self.ii.configure_dac_channel(1, 1)
        self.ii.write_dac(255)
        time.sleep(0.5)
        leds = self.ii.read_port(0)
        t0 = time.time()
        while( (time.time() - t0 < 1) and leds == 0):
            leds = self.ii.read_port(0)
        if leds == 0:
            self.comment("Could not find non-zero LED pattern after 1 second")
            return 0
        self.comment("Found {l:#x} on LEDs".format(l = leds))
        if leds > 245:
            self.comment("Value is high enough. Now checking timing")
        else:
            self.comment("Value not correct: 0/3")
            return 0
        timing = round(self.ii.transition_timing(0x0, leds), 3)
        self.comment("Timing should be 0.1 and found to be {t}".format(t = timing))
        if timing > 0.1*1.12 or timing < 0.1/1.12:
            self.comment("Timing very out. 0/3")
            return 0
        elif timing > 0.1*1.06 or timing < 0.1/1.06:
            self.comment("Timing marginal. At most 2/3")
            timing_marginal = True
        else:
            self.comment("Timing good")

        self.comment("Asserting volatage such that LEDs should be flashing between 0 and 0x40")
        self.ii.configure_dac_channel(0, 0)
        self.ii.configure_dac_channel(1, 1)
        self.ii.write_dac(0x40)
        time.sleep(0.5)
        leds = self.ii.read_port(0)
        t0 = time.time()
        while( (time.time() - t0 < 5) and leds == 0):
            leds = self.ii.read_port(0)
        if leds == 0:
            self.comment("Could not find non-zero LED pattern after 1 second")
            return 0
        self.comment("Found {l:#x} on LEDs".format(l = leds))
        if leds > 0x39 and leds < 0x47:
            self.comment("Value is high enough. Now checking timing")
        else:
            self.comment("Value not correct: 0/3")
            return 0
        timing = round(self.ii.transition_timing(0x0, leds), 3)
        self.comment("Timing should be 0.1 and found to be {t}".format(t = timing))
        if timing > 0.1*1.12 or timing < 0.1/1.12:
            self.comment("Timing very out. 0/3")
            return 0
        elif timing > 0.1*1.06 or timing < 0.1/1.06:
            self.comment("Timing marginal. At most 2/3")
            timing_marginal = True
        else:
            self.comment("Timing good")
        if timing_marginal == True:
            self.comment("Marginal timing: mark = 2/3")
            return 2
        self.comment("All timing good. 3/3")
        return 3



