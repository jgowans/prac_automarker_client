import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError, SourceFileProblem
import interrogator_interface
import gdb_interface
import zipfile

class PracExam2Part2Tests(PracTests):

    def catalogue_submission_files(self):
        os.chdir(self.submitter.submission_directory)
        all_files = os.listdir()
        self.submitter.makefiles = [f for f in all_files if f.lower() == 'makefile']
        self.submitter.ldfiles = [f for f in all_files if f.endswith(".ld")]
        self.submitter.sfiles = [f for f in all_files if f.endswith(".s")]
        self.submitter.files_to_mark = \
            self.submitter.makefiles + \
            self.submitter.ldfiles + \
            self.submitter.sfiles
        self.logger.info("Selected for marking: {f}".format(f = self.submitter.files_to_mark))
        self.submitter.files_for_plag_check = \
            self.submitter.sfiles

    def prebuild(self):
        for sfile in self.submitter.sfiles:
            cmd = "sed -i \"s/.word 0xFACEB00C/.word 0x55AA55AA\\n .word 0x55AA55AA\\n .word 0x55AA55AA\\n/g\" {f}".format(f = sfile)
            self.exec_as_marker(cmd)
        self.logger.info("Replaced 0xFACEB00C with .word 0x55AA55AA .word 0x55AA55AA .word 0x55AA55AA.")
        self.logger.info("Smallest value should now be 0x42")

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
            self.logger.info("----------- PART 2 ----------------")
            self.part_2_tests()
        except TestFailedError as e:
            self.logger.critical("A test failed. Marking cannot continue")
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
        except gdb_interface.GDBException as e:
            self.logger.critical("Your program did not respond the way GDB expected it to")

    def part_2_tests(self):
        self.gdb.send_continue()
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("LEDs found to show: {l:#x}".format(l = leds))
        if leds == 0x42:
            self.submitter.increment_mark(1.5)
        else:
            self.logger.critical("Incorrect")
            raise TestFailedError
        self.logger.info("Now testing if it can find the smallest value when it's the last byte")
        self.gdb.send_control_c()
        for sfile in self.submitter.sfiles:
            cmd = "sed -i \"s/.word 0xCAFEBABE/.word 0x0708090A/g\" {f}".format(f = sfile)
            self.exec_as_marker(cmd)
            self.logger.info("Replaced 0xCAFEBABE with 0x0708090A. Smallest value should now be 0x07")
        self.logger.info("Running 'make' in submission directory")
        try:
            self.exec_as_marker("make -B")
        except BuildFailedError as e:
            self.logger.info("Received build error. Aborting")
            raise BuildFailedError
        try:
            self.gdb.load()
        except gdb_interface.CodeLoadFailed as e:
            return
        try:
            self.gdb.verify()
        except gdb_interface.CodeVerifyFailed as e:
            return
        self.gdb.send_continue()
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("LEDs found to show: {l:#x}".format(l = leds))
        if leds == 0x07:
            self.submitter.increment_mark(0.5)
        else:
            self.logger.critical("Incorrect")
