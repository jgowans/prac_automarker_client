import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError, SourceFileProblem
import interrogator_interface
import gdb_interface
import zipfile

class PracExam2Part3Tests(PracTests):

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
        self.gdb.open_file(self.elf_file)
        self.gdb.connect()
        self.gdb.erase()
        self.gdb.soft_reset()
        self.ii.highz_pin(0)
        self.ii.highz_pin(1)
        self.ii.highz_pin(2)
        self.ii.highz_pin(3)
        self.ii.write_dac(0, 0)
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
        except gdb_interface.BreakpointNotHit as e:
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
        self.logger.info("Checking if LEDs are counting down by 1")
        self.ii.write_dac(1, 0x80)
        self.gdb.send_continue()
        leds = self.ii.read_port(0)
        try:
            self.logger.info("Looking for transition: {a:#x} -> {b:#x}".format(a = (leds-1)%0x100, b = (leds-2)%0x100))
            timing = round(self.ii.timing_transition((leds-1)%0x100, (leds-2)%0x100), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("Could not find incrementing transition")
            raise TestFailedError
        self.logger.info("Correct.")
        self.submitter.increment_mark(0.5)
        self.logger.info("Now checking timing")
        to_test = [0x20, 0xB0, 0x90]
        for dac1 in to_test:
            self.ii.write_dac(1, dac1)
            expected = round(0.5 + ((dac1/0xFF) * (2.0 - 0.5)), 2)
            self.logger.info("Wrote {d1:.2} V to POT1.".format(d1 = 3.3*dac1/0xFF))
            self.logger.info("Expected timing of 0.5 + ({v:.2}V/3.3 V)*(2.0-0.5) = {e} s".format(v = 3.3*dac1/0xFF, e = expected))
            time.sleep(0.1)
            leds = self.ii.read_port(0)
            try:
                self.logger.info("Looking for transition: {a:#x} -> {b:#x}".format(a = (leds-1)%0x100, b = (leds-2)%0x100))
                timing = round(self.ii.timing_transition((leds-1)%0x100, (leds-2)%0x100), 2)
                self.logger.info("Found timing of: {t} seconds".format(t = timing))
                if (timing > (expected*0.95)-0.1 and timing < (expected*1.05)+0.1):
                    self.logger.info("Correct.")
                    self.submitter.increment_mark(0.5)
            except interrogator_interface.LEDTimingTimeout as e:
                self.logger.critical("Could not find incrementing transition")
