import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError, SourceFileProblem
import interrogator_interface
import gdb_interface
import zipfile

class PracExam2Part0Tests(PracTests):
    def catalogue_submission_files(self):
        os.chdir(self.submitter.submission_directory)
        all_files = os.listdir()
        self.submitter.makefiles = [f for f in all_files if f.lower() == 'makefile']
        self.submitter.ldfiles = [f for f in all_files if f.endswith(".ld")]
        self.submitter.sfiles = [f for f in all_files if f.endswith(".s")]
        self.submitter.files_to_mark = self.submitter.makefiles + \
            self.submitter.ldfiles + \
            self.submitter.sfiles
        self.logger.info("Selected for marking: {f}".format(f = self.submitter.files_to_mark))
        self.submitter.files_for_plag_check = \
            self.submitter.sfiles

    def run_specific_prac_tests(self):
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
            self.logger.info("----------- PART 1 ----------------")
            self.part_0_tests()
        except TestFailedError as e:
            self.logger.critical("A test failed. Marking cannot continue")
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
        except gdb_interface.GDBException as e:
            self.logger.critical("Your program did not respond the way GDB expected it to")

    def part_0_tests(self):
        self.gdb.send_continue()
        patterns = [12, 7, 15, 1, 9, 0]
        for pattern in patterns:
            self.ii.highz_pin(0)
            self.ii.highz_pin(1)
            self.ii.highz_pin(2)
            self.ii.highz_pin(3)
            sw0 = True if pattern & 0b0001 != 0 else False
            sw1 = True if pattern & 0b0010 != 0 else False
            sw2 = True if pattern & 0b0100 != 0 else False
            sw3 = True if pattern & 0b1000 != 0 else False
            if sw0 == True:
                self.ii.clear_pin(0)
            if sw1 == True:
                self.ii.clear_pin(1)
            if sw2 == True:
                self.ii.clear_pin(2)
            if sw3 == True:
                self.ii.clear_pin(3)
            self.logger.info("Pushing the following: SW0: {0}, SW1: {1}, SW2: {2}, SW3: {3}".format(
                sw0, sw1, sw2, sw3))
            self.logger.info("Expecting value: {v}".format(v = pattern))
            time.sleep(0.1)
            leds = self.ii.read_port(0)
            self.logger.info("Got value: {v}".format(v = leds))
            if leds == pattern:
                self.submitter.increment_mark(0.25)
            else:
                self.logger.info("Incorrect")

