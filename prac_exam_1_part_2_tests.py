import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError, SourceFileProblem
import interrogator_interface
import gdb_interface
import zipfile

class PracExam1Part2Tests(PracTests):

    def catalogue_submission_files(self):
        os.chdir(self.submitter.submission_directory)
        all_files = os.listdir()
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

    def build(self):
        self.clean_marker_directory()
        os.chdir('/home/marker/')
        for f in self.submitter.files_to_mark:
            cmd = "cp \"{d}/{f}\" /home/marker/".format(d = self.submitter.submission_directory, f = f)
            self.exec_as_marker(cmd)
        for f in self.submitter.sourcefiles:
            cmd = "sed -i \"s/0x42, 0x69, 0x12, 0xCC, 0xBB, 0x55, 0xA1, 0x33, 0x1A, 0xDF, 0x56/0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xD7, 0xBB, 0xA1/g\" {f}".format(f = f)
            self.exec_as_marker(cmd)
        self.logger.info("Replaced array with:")
        self.logger.info("0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xD7, 0xBB, 0xA1")
        self.logger.info("Largest value should be 0xD7 and smallest should be 0xA1")
        self.logger.info("Running 'make' in submission directory")
        try:
            self.exec_as_marker("make -B")
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
        self.logger.info("Not holding SW0, LEDs should show 0xD7")
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("LEDs displaying: {l:#x}".format(l = leds))
        if leds == 0xD7:
            self.logger.info("Correct")
            self.submitter.increment_mark(1)
        else:
            self.logger.critical("Incorrect")
        self.logger.info("Holding SW0, LEDs should show 0xA1")
        self.ii.clear_pin(0)
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("LEDs displaying: {l:#x}".format(l = leds))
        if leds == 0xA1:
            self.logger.info("Correct")
            self.submitter.increment_mark(1)
        else:
            self.logger.critical("Incorrect")

