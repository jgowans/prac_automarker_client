import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError, SourceFileProblem
import interrogator_interface
import gdb_interface
import zipfile

class PracExam2Part4Tests(PracTests):

    def catalogue_submission_files(self):
        os.chdir(self.submitter.submission_directory)
        all_files = os.listdir()
        self.logger.info("After unzip, directory contains: {f}".format(f = all_files))
        self.submitter.makefiles = [f for f in all_files if f.lower() == 'makefile']
        self.submitter.sourcefiles = [f for f in all_files if f.endswith(".c")]
        self.submitter.ldfiles = [f for f in all_files if f.endswith(".ld")]
        self.submitter.sfiles = [f for f in all_files if f.endswith(".s")]
        self.submitter.headerfiles = [f for f in all_files if f.endswith(".h")]
        self.submitter.files_to_mark = \
            self.submitter.makefiles + \
            self.submitter.sourcefiles + \
            self.submitter.ldfiles + \
            self.submitter.sfiles + \
            self.submitter.headerfiles
        self.logger.info("Selected for marking: {f}".format(f = self.submitter.files_to_mark))
        self.submitter.files_for_plag_check = \
            self.submitter.sourcefiles + \
            self.submitter.headerfiles

    def run_specific_prac_tests(self):
        self.patterns = [0x08, 0x18, 0x1C, 0x3C, 0x3E, 0x7E, 0x7F, 0xFF]
        self.gdb.open_file(self.elf_file)
        self.gdb.connect()
        self.gdb.erase()
        self.gdb.soft_reset()
        self.ii.highz_pin(0)
        self.ii.highz_pin(1)
        self.ii.highz_pin(2)
        self.ii.highz_pin(3)
        try:
            self.gdb.load()
        except gdb_interface.CodeLoadFailed as e:
            return
        try:
            self.gdb.verify()
        except gdb_interface.CodeVerifyFailed as e:
            return
        try:
            self.logger.info("----------- PART 4 ----------------")
            self.part_4_tests()
        except TestFailedError as e:
            self.logger.critical("A test failed. Marking cannot continue")
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
        except gdb_interface.GDBException as e:
            self.logger.critical("Your program did not respond the way GDB expected it to")

    def get_idx(self, val):
        try:
            idx = self.patterns.index(val)
        except ValueError as e:
            self.logger.info("LEDs were showing {v:#x} which is not a valid pattern".format(v = val))
            raise TestFailedError
        return idx

    def get_pattern(self, idx):
        return self.patterns[idx%len(self.patterns)]


    def idx_difference(self, larger, smaller):
        if larger >= smaller:
            return larger - smaller
        else:
            return larger + len(self.patterns) - smaller

    def part_4_tests(self):
        self.gdb.send_continue()
        time.sleep(0.3)
        leds = self.ii.read_port(0)
        self.logger.info("Initial pattern found to be: {l:#x}".format(l = leds))
        leds_before = self.ii.read_port(0)
        idx_before = self.get_idx(leds_before)
        self.logger.info("Asserting a single, clean pulse on SW1. LEDs should go to next index")
        self.ii.clear_pin(1)
        time.sleep(0.3)
        self.ii.highz_pin(1)
        time.sleep(0.3)
        leds_after = self.ii.read_port(0)
        idx_after = self.get_idx(leds_after)
        self.logger.info("After clean pulse, LEDs showing {l:#x} with index {i}".format(l = leds_after, i = idx_after))
        delta_idx = self.idx_difference(idx_after, idx_before)
        self.logger.info("That's a change of: {i}".format(i = delta_idx))
        if delta_idx == 1:
            self.submitter.increment_mark(0.5)
        else:
            self.logger.error("Incorrect")
        leds_before = leds_after
        idx_before = idx_after
        self.logger.info("Now checking it's the right edge. Asserting a clean falling edge. Should increment")
        self.ii.clear_pin(1)
        time.sleep(0.3)
        leds_after = self.ii.read_port(0)
        idx_after = self.get_idx(leds_after)
        self.logger.info("After clean falling edge, LEDs showing: {l:#x} with index: {i}".format(l = leds_after, i = idx_after))
        delta_idx = self.idx_difference(idx_after, idx_before)
        self.logger.info("That's a change of: {delta}".format(delta = delta_idx))
        if delta_idx == 1:
            self.logger.info("Correct. Now checking nothing happens when a clean rising edge is occurs")
            leds_before = leds_after
            idx_before = idx_after
            self.ii.highz_pin(1)
            time.sleep(0.3)
            leds_after = self.ii.read_port(0)
            idx_after = self.get_idx(leds_after)
            self.logger.info("After clean rising edge, LEDs showing: {l:#x} with index: {i}".format(l = leds_after, i = idx_after))
            delta_idx = self.idx_difference(idx_after, idx_before)
            self.logger.info("That's a change of: {delta}".format(delta = delta_idx))
            if delta_idx == 0:
                self.logger.info("Correct")
                self.submitter.increment_mark(0.5)
        self.logger.info("Now checking noisy eges are properly debounced.")
        self.logger.info("Asserting a noisy falling and noisy rising edge. LEDs should only change once")
        leds_before = self.ii.read_port(0)
        idx_before = self.get_idx(leds_before)
        self.ii.clear_pin(1)
        self.ii.highz_pin(1)
        self.ii.clear_pin(1)
        self.ii.highz_pin(1)
        self.ii.clear_pin(1)
        time.sleep(0.5)
        self.ii.highz_pin(1)
        self.ii.clear_pin(1)
        self.ii.highz_pin(1)
        self.ii.clear_pin(1)
        self.ii.highz_pin(1)
        time.sleep(0.5)
        leds_after = self.ii.read_port(0)
        idx_after = self.get_idx(leds_after)
        self.logger.info("After noisy press, LEDs showing: {l:#x} with index: {i}".format(l = leds_after, i = idx_after))
        delta_idx = self.idx_difference(idx_after, idx_before)
        self.logger.info("That's a change of: {delta}".format(delta = delta_idx))
        if delta_idx == 1:
            self.submitter.increment_mark(0.5)
        else:
            self.logger.error("Incorrect")
        self.logger.info("Now checking for wrapping. Pressing button until last element is shown")
        for _ in range(10):
            self.ii.clear_pin(1)
            time.sleep(0.3)
            self.ii.highz_pin(1)
            time.sleep(0.3)
            if self.ii.read_port(0) == self.patterns[-1]:
                break
        leds = self.ii.read_port(0)
        if leds != self.patterns[-1]:
            self.logger.error("Could not find last pattern")
            return
        self.logger.info("LEDs showing last pattern. Doing one clean press to check it goes to pattern 0")
        self.ii.clear_pin(1)
        time.sleep(0.3)
        self.ii.highz_pin(1)
        time.sleep(0.3)
        leds = self.ii.read_port(0)
        idx = self.get_idx(leds)
        self.logger.info("LEDs displaying {l:#x} with index {i}".format(l = leds, i = idx))
        if idx == 0:
            self.logger.info("Wrapped correctly!")
            self.submitter.increment_mark(0.5)
        else:
            self.logger.error("Incorrect")
