import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError, SourceFileProblem
import interrogator_interface
import gdb_interface
import zipfile

class PracExam1Part1Tests(PracTests):

    def catalogue_submission_files(self):
        os.chdir(self.submitter.submission_directory)
        all_files = os.listdir()
        self.submitter.makefiles = [f for f in all_files if f.lower() == 'makefile']
        self.submitter.ldfiles = [f for f in all_files if f.endswith(".ld")]
        self.submitter.sfiles = [f for f in all_files if f.endswith(".s")]
        self.submitter.files_to_mark = \
            self.submitter.makefiles + \
            self.submitter.ldfiles + \
            self.submitter.sfiles + \
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
        to_test = [(0x20, 0xB0), (0x50, 0x90), (0xBA, 0x50), (0x10, 0x40)]
        for dac0, dac1 in to_test:
            self.ii.write_dac(0, dac0)
            self.ii.write_dac(1, dac1)
            larger = max(dac0, dac1)
            self.logger.info("Wrote {d0:#x} to POT0 and {d1:#x} to POT1".format(d0 = dac0, d1 = dac1))
            self.logger.info("LEDs expected to show: {larger:#x}".format(larger = larger))
            time.sleep(0.1)
            leds = self.ii.read_port(0)
            self.logger.info("LEDs found to show: {leds:#x}".format(leds = leds))
            if (leds > ((expected*0.95) - 5)) and (leds < ((expected*1.05) + 2)):
                self.submitter.increment_mark(0.5)
            else:
                self.logger.error("Incorrect")
