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
        self.logger.info("Running 'make' in submission directory")
        try:
            self.exec_as_marker("make")
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
            self.logger.info("----------- PART 1 ----------------")
            self.part_1_tests()
        except TestFailedError as e:
            self.logger.critical("A test failed. Marking cannot continue")
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
        except gdb_interface.GDBException as e:
            self.logger.critical("Your program did not respond the way GDB expected it to")

    def part_1_tests(self):
        self.gdb.send_continue()
        time.sleep(0.1)
        leds_before = self.ii.read_port(0)
        self.logger.info("Leds should show 0x0A, found to show: {l:#x}".format(l = leds_before))
        if leds_before == 0x0A:
            self.submitter.increment_mark(0.5)
        else:
            self.logger.info("Incorrect")
        self.logger.info("Running a stream of 10 clean button press-releases")
        for _ in range(10):
            self.ii.clear_pin(0)
            time.sleep(0.2)
            self.ii.highz_pin(0)
            time.sleep(0.2)
        self.logger.info("LEDs should show {before:#x} + 10 = {expected:#x}".format(before = leds_before, expected = leds_before + 10))
        leds_after = self.ii.read_port(0)
        self.logger.info("LEDs found to show {l:#x}".format(l = leds_after))
        if leds_before + 10 == leds_after:
            self.submitter.increment_mark(0.5)
        elif leds_before == leds_after:
            self.logger.critical("LEDs are not changing. Cannot continue")
            raise TestFailedError
        else:
            self.logger.critical("Incorrect")
        leds_before = leds_after
        self.logger.info("Asserting a noisy falling edge on SW0. Nothing should happen")
        self.ii.clear_pin(0)  # about 2.5 ms between each transition.
        self.ii.highz_pin(0)
        self.ii.clear_pin(0)
        self.ii.highz_pin(0)
        self.ii.clear_pin(0)
        time.sleep(0.1)
        leds_after = self.ii.read_port(0)
        self.logger.info("After edge, LEDs showing: {l:#x}".format(l = leds_after))
        if leds_before == leds_after:
            self.logger.info("Correctly dealt with noisy falling edge")
            self.submitter.increment_mark(0.5)
        else:
            self.logger.critical("LEDs changed. Incorrect")
        leds_before = leds_after
        self.logger.info("Asserting a noisy rising edge on SW0. LEDs should increment by 1")
        ledse = self.ii.read_port(0)
        self.ii.highz_pin(0)
        self.ii.clear_pin(0)
        self.ii.highz_pin(0)
        self.ii.clear_pin(0)
        self.ii.highz_pin(0)
        time.sleep(0.1)
        leds_after = self.ii.read_port(0)
        self.logger.info("After edge, LEDs showing: {l:#x}".format(l = leds_after))
        if leds_before + 1 == leds_after:
            self.logger.info("Correct")
            self.submitter.increment_mark(0.5)
        else:
            self.logger.critical("Incorrect")

