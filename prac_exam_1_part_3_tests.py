import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError, SourceFileProblem
import interrogator_interface
import gdb_interface
import zipfile

class PracExam1Part3Tests(PracTests):

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
            src = "{d}/{f}".format(d = self.submitter.submission_directory, f = f)
            src = src.replace("'", "'\\''")
            cmd = "cp \"{src}\" /home/marker/".format(src = src, f = f)
            self.exec_as_marker(cmd)
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
        self.ii.write_dac(0, 0)
        self.ii.write_dac(1, 0x10)
        try:
            self.gdb.load()
        except gdb_interface.CodeLoadFailed as e:
            return
        try:
            self.gdb.verify()
        except gdb_interface.CodeVerifyFailed as e:
            return
        try:
            self.logger.info("----------- PART 3 ----------------")
            self.part_3_tests()
        except TestFailedError as e:
            self.logger.critical("A test failed. Marking cannot continue")
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
        except gdb_interface.GDBException as e:
            self.logger.critical("Your program did not respond the way GDB expected it to")

    def part_3_tests(self):
        self.gdb.send_continue()
        time.sleep(0.1)
        self.logger.info("Checking that the timer is running and generating interrupts")
        self.gdb.send_control_c()
        tim6_isr_addr = self.gdb.read_word(0x08000000 + 0x84)
        try:
            self.gdb.run_to_address(tim6_isr_addr & 0xFFFFFFFE)
        except Exception as e:
            self.logger.exception(e)
            self.logger.critical("TIM6 does not seem to be running. Exiting tests")
            return
        self.gdb.send_continue()
        time.sleep(0.1)
        self.gdb.send_control_c()
        first_cnt = self.gdb.read_word(0x40001000 + 0x24)
        self.gdb.send_continue()
        time.sleep(0.1)
        self.gdb.send_control_c()
        second_cnt = self.gdb.read_word(0x40001000 + 0x24)
        if first_cnt == second_cnt:
            self.logger.critical("TIM6 does not seem to be running as CNT not counting. Leaving test")
            raise TestFailedError
        self.logger.info("TIM6 seems to be running.")
        self.submitter.increment_mark(1)
        self.logger.info("Checking if LEDs are counting up by 1")
        self.ii.write_dac(0, 0)
        self.ii.write_dac(1, 0x10)
        self.gdb.send_continue()
        leds = self.ii.read_port(0)
        try:
            self.logger.info("Looking for transition: {a:#x} -> {b:#x}".format(a = leds+2, b = leds+3))
            timing = round(self.ii.timing_transition(leds+2, leds+3), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("Could not find incrementing transition")
            raise TestFailedError
        self.logger.info("Correct.")
        self.submitter.increment_mark(0.5)
        self.logger.info("Now checking timing")
        to_test = [(0x20, 0x20), (0xB0, 0xB0), (0x50, 0x90), (0xBA, 0x20), (0x10, 0x40)]
        for dac0, dac1 in to_test:
            self.ii.write_dac(0, dac0)
            self.ii.write_dac(1, dac1)
            larger_dac = max(dac0, dac1)
            expected = round(0.3 + ((larger_dac/0xFF) * (2.5 - 0.3)), 2)
            self.logger.info("Wrote {d0:.2} V to POT0 and {d1:.2} V to POT1.".format(d0 = 3.3*dac0/0xFF, d1 = 3.3*dac1/0xFF))
            self.logger.info("Expected timing of 0.3 + ({v:.2}V/3.3 V)*(2.5-0.3) = {e} s".format(v = 3.3*larger_dac/0xFF, e = expected))
            time.sleep(0.1)
            leds = self.ii.read_port(0)
            try:
                self.logger.info("Looking for transition: {a:#x} -> {b:#x}".format(a = leds+1, b = leds+2))
                timing = round(self.ii.timing_transition(leds+1, leds+2), 2)
                self.logger.info("Found timing of: {t} seconds".format(t = timing))
                if (timing > expected-0.13 and timing < expected+0.13):
                    self.logger.info("Correct.")
                    self.submitter.increment_mark(0.5)
            except interrogator_interface.LEDTimingTimeout as e:
                self.logger.critical("Could not find incrementing transition")
