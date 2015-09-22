import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError, SourceFileProblem
import interrogator_interface
import gdb_interface
import zipfile

class Prac6Tests(PracTests):
    def catalogue_submission_files(self):
        os.chdir(self.submitter.submission_directory)
        all_files = os.listdir()
        self.logger.info("Before unzip, directory contains: {f}".format(f = all_files))
        zip_files = [fi for fi in all_files if fi.endswith(".zip")]
        if len(zip_files) != 1:
            self.logger.critical("Too many or not enough zip files found out of: {a}. Aborting.".format(a = all_files))
            raise SourceFileProblem
        self.logger.info("Extracting zipfile: {z}".format(z = zip_files[0]))
        with zipfile.ZipFile(zip_files[0]) as z:
            z.extractall()
        all_files = os.listdir()
        self.logger.info("After unzip, directory contains: {f}".format(f = all_files))
        self.submitter.makefiles = [f for f in all_files if f.lower() == 'makefile']
        if len(self.submitter.makefiles) != 1:
            self.logger.critical("Too few or too many makefiles submitted")
            raise SourceFileProblem
        self.submitter.sourcefiles = [f for f in all_files if f.endswith(".c")]
        if len(self.submitter.sourcefiles) != 1:
            self.logger.critical("Too few or too many source files submitted")
            raise SourceFileProblem
        self.submitter.ldfiles = [f for f in all_files if f.endswith(".ld")]
        if len(self.submitter.ldfiles) != 1:
            self.logger.critical("Too few or too many linker scripts submitted")
            raise SourceFileProblem
        self.submitter.sfiles = [f for f in all_files if f.endswith(".s")]
        if len(self.submitter.sfiles) != 1:
            self.logger.critical("Too many or too few assembly files submitted")
            raise SourceFileProblem
        self.submitter.files_to_mark = \
            self.submitter.makefiles + \
            self.submitter.sourcefiles + \
            self.submitter.ldfiles + \
            self.submitter.sfiles
        self.logger.info("Selected for marking: {f}".format(f = self.submitter.files_to_mark))
        self.submitter.files_for_plag_check = \
            self.submitter.makefiles + \
            self.submitter.sourcefiles + \
            self.submitter.ldfiles

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
        self.gdb.load()
        self.gdb.verify()
        self.ii.highz_pin(0)
        self.ii.highz_pin(1)
        self.ii.highz_pin(2)
        self.ii.highz_pin(3)
        self.ii.write_dac(0, 0)
        self.ii.write_dac(1, 0)
        try:
            self.logger.info("----------- PART 1 ----------------")
            self.part_1_tests()
            self.logger.info("----------- PART 2 ----------------")
            self.part_2_tests()
        except TestFailedError as e:
            self.logger.critical("A test failed. Marking cannot continue")
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
        except gdb_interface.GDBException as e:
            self.logger.critical("Your program did not respond the way GDB expected it to")

    def part_1_tests(self):
        self.gdb.send_continue()
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("Found on LEDs: {l:#x}".format(l = leds))
        if leds != 0xA0:
            self.logger.critical("Incorrect.")
            return
        self.logger.info("Correct")
        self.submitter.increment_mark(2)

    def part_2_tests(self):
        self.gdb.send_control_c()
        first_read = self.gdb.read_word(0x200000F0)
        self.logger.info("Contents of address 0x2000 00F0: {v:#x}".format(v = first_read))
        self.gdb.send_continue()
        time.sleep(0.1)
        self.gdb.send_control_c()
        second_read = self.gdb.read_word(0x200000F0)
        self.logger.info("Contents changed to: {v:#x}".format(v = second_read))
        if first_read == second_read:
            self.logger.critical("No change. Exiting")
            raise TestFailedError
        self.logger.info("Correct. Now checking LED timing")
        leds = self.ii.read_port(0)
        self.logger.info("Looking for transition {p0:#x} -> {p1:#x}".format(
            p0 = leds+1, p1 = leds+2))
        self.gdb.send_continue()
        try:
            timing = round(self.ii.timing_transition(leds+1, leds+2), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("Could not find incrementing transition")
            return
        self.logger.info("Found transition. Timing should be 1 second. Found to be: {t} second".format(t = timing))
        if (timing > 1*0.95 and timing < 1*1.05):
            self.logger.info("Correct.")
            self.submitter.increment_mark(2)
        elif (timing > 1*0.90 and timing < 1*1.10):
            self.logger.info("Not good enough. Half marks.")
            self.submitter.increment_mark(1)
        else:
            self.logger.critical("Too far out. Not awarding marks")
            return
