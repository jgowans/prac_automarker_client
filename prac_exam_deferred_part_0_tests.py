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
            self.logger.info("----------- PART 0 ----------------")
            self.part_0_tests()
        except TestFailedError as e:
            self.logger.critical("A test failed. Marking cannot continue")
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
        except gdb_interface.GDBException as e:
            self.logger.critical("Your program did not respond the way GDB expected it to")

    def part_0_tests(self):
        self.gdb.send_continue()
        patterns = [0x81, 0x42, 0x24, 0x18]
        for idx in range(6):
            a = patterns[idx % len(patterns)]
            b = patterns[(idx+1) % len(patterns)]
            try:
                self.logger.info("Looking for transition: {a:#x} -> {b:#x}".format(a = a, b = b))
                timing = round(self.ii.timing_transition(a, b), 2)
            except interrogator_interface.LEDTimingTimeout as e:
                self.logger.critical("Could not find incrementing transition")
                continue
            self.logger.info("Found transition with timing: {t} seconds".format(t = timing))
            if timing > 1.1 or timing < 0.9:
                self.submitter.increment_mark(0.25)
            else:
                self.submitter.increment_mark(0.5)

