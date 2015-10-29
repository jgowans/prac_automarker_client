import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError, SourceFileProblem
import interrogator_interface
import gdb_interface
import zipfile

class Prac9Tests(PracTests):

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
            cmd = "sed -i \"s/{{0x00, 0x81, 0xC3, 0xE7, 0xFF, 0x7E, 0x3C, 0x18}}/{{0x42, 0x69, 0xAA, 0xBB, 0xA1}}/g\" {f}".format(f = f)
            self.exec_as_marker(cmd)
            cmd = "sed -i \"s/{{0x81, 0xC3, 0xE7, 0xFF, 0x7E, 0x3C, 0x18, 0x00}}/{{0x42, 0x69, 0xAA, 0xBB, 0xA1}}/g\" {f}".format(f = f)
            self.exec_as_marker(cmd)
        self.logger.info("Replaced array with {0x42, 0x69, 0xAA, 0xBB, 0xA1}")
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
            self.patterns = [0x42, 0x69, 0xAA, 0xBB, 0xA1]
            self.logger.info("----------- PART 1 ----------------")
            self.part_1_tests()
            self.logger.info("----------- PART 2 ----------------")
            self.part_2_tests()
            self.logger.info("----------- PART 3 ----------------")
            self.part_3_tests()
            self.logger.info("----------- PART 4 ----------------")
            self.part_4_tests()
        except TestFailedError as e:
            self.logger.critical("A test failed. Marking cannot continue")
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
        except gdb_interface.GDBException as e:
            self.logger.critical("Your program did not respond the way GDB expected it to")

    def get_index(self, val):
        try:
            idx = self.patterns.index(val)
        except ValueError as e:
            self.logger.info("LEDs were showing {v:#x} which is not a valid pattern".format(v = val))
            raise TestFailedError
        return idx

    def get_pattern(self, idx):
        return self.patterns[idx%len(self.patterns)]

    def part_1_tests(self):
        self.gdb.send_continue()
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("Leds should show 0x42, found to show: {l:#x}".format(l = leds))
        if leds == 0x42:
            self.submitter.increment_mark(1)
        else:
            self.logger.info("Incorrect")

    def part_2_tests(self):
        self.ii.clear_pin(0)
        self.logger.info("Asserting SW0")
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
        self.logger.info("TIM6 seems to be running. Now checking timing")
        leds = self.ii.read_port(0)
        idx = self.get_index(leds)
        self.gdb.send_continue()
        try:
            self.logger.info("Looking for transition: {a:#x} -> {b:#x}".format(
                a = self.get_pattern(idx+1), b = self.get_pattern(idx+2)))
            timing = round(self.ii.timing_transition(self.get_pattern(idx+1), self.get_pattern(idx+2)), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("Could not find incrementing transition")
            return
        self.logger.info("Found transition. Timing should be 0.5 second. Found to be: {t} second".format(t = timing))
        if (timing > 0.5*0.95 and timing < 0.5*1.05):
            self.logger.info("Correct.")
            self.submitter.increment_mark(2)
        elif (timing > 0.5*0.90 and timing < 0.5*1.10):
            self.logger.info("Too far out. Partial marks.")
            self.submitter.increment_mark(1)
        else:
            self.logger.critical("Too far out. Not awarding marks")
        t0 = time.time()
        self.logger.info("Checking that it wrapps back around to element 0")
        while(True):
            if (self.ii.read_port(0) == self.patterns[-1]):
                break
            if (time.time() - t0 > 10):
                self.logger.critical("Could not find last pattern in sequence. Aborting")
                raise TestFailedError
        time.sleep(0.75)
        leds = self.ii.read_port(0)
        self.logger.info("After last pattern in array, LEDs went to: {l:#x}".format(l = leds))
        if leds != self.patterns[0]:
            self.logger.critical("Not correct! Remember that the marker changes the length of the array at compile time")
            raise TestFailedError
        self.logger.info("Correct.")
        self.submitter.increment_mark(1)

    def part_3_tests(self):
        self.ii.highz_pin(0)
        self.logger.info("Released SW0. Checking that LEDs do not change")
        leds = self.ii.read_port(0)
        time.sleep(3)
        leds_after = self.ii.read_port(0)
        if leds != leds_after:
            self.logger.info("They continued to change. Incorrect. Cannot continue marking part 3")
            return
        self.logger.info("LEDs stopped counting. Good.")
        idx = self.get_index(leds)
        self.logger.info("Before edge, LEDs are displaying {l:#x}, with index {i}".format(l = leds, i = idx))
        self.logger.info("Asserting a clean falling and clean rising edge on SW1")
        self.ii.clear_pin(1)
        time.sleep(0.2)
        self.ii.highz_pin(1)
        time.sleep(0.1)
        leds_after = self.ii.read_port(0)
        idx_after = self.get_index(leds_after)
        self.logger.info("After edge, LEDs showing: {l:#x} or index: {i}".format(l = leds_after, i = idx_after))
        if ((idx + 1)%len(self.patterns)) == idx_after:
            self.logger.info("Correctly dealt with clean edges")
            self.submitter.increment_mark(1)
        else:
            self.logger.critical("LEDs did not go to NEXT pattern")
        leds = leds_after
        idx = idx_after
        self.logger.info("Asserting a noisy falling edge on SW1")
        self.ii.clear_pin(1)  # about 2.5 ms between each transition.
        self.ii.highz_pin(1)
        self.ii.clear_pin(1)
        self.ii.highz_pin(1)
        self.ii.clear_pin(1)
        time.sleep(0.1)
        leds_after = self.ii.read_port(0)
        idx_after = self.get_index(leds_after)
        self.logger.info("After edge, LEDs showing: {l:#x} or index: {i}".format(l = leds_after, i = idx_after))
        if ((idx + 1)%len(self.patterns)) == idx_after:
            self.logger.info("Correctly dealt with noisy falling edge")
            self.submitter.increment_mark(1)
        else:
            self.logger.critical("LEDs changed by too much. No debouncing done?")
            return
        leds = leds_after
        idx= idx_after
        self.logger.info("Asserting a noisy rising edge on SW1. Nothing should happen.")
        ledse = self.ii.read_port(0)
        self.ii.highz_pin(1)
        self.ii.clear_pin(1)
        self.ii.highz_pin(1)
        self.ii.clear_pin(1)
        self.ii.highz_pin(1)
        time.sleep(0.1)
        leds_after = self.ii.read_port(0)
        self.logger.info("After edge, LEDs showing: {l:#x}".format(l = leds_after))
        if leds == leds_after:
            self.logger.info("Correct")
            self.submitter.increment_mark(1)
        else:
            self.logger.critical("LEDs changed.  Bad.")

    def part_4_tests(self):
        leds_before = self.ii.read_port(0)
        self.logger.info("Before holding SW2, LEDs showing: {l:#x}".format(l = leds_before))
        self.logger.info("Asserting SW2")
        self.ii.clear_pin(2)
        to_test = [(0x60, 0xC0), (0xF0, 0x40), (0x80, 0xF0)]
        for dac0, dac1 in to_test:
            self.ii.write_dac(0, dac0)
            self.ii.write_dac(1, dac1)
            expected = min(dac0, dac1)
            self.logger.info("Wrote {d0:#x} to POT0 and {d1:#x} to POT1.".format(d0 = dac0, d1 = dac1))
            time.sleep(0.1)
            leds = self.ii.read_port(0)
            self.logger.info("Expected: {e:#x}, found: {f:#x}".format(e = expected, f = leds))
            if (leds > expected+5) or (leds < expected-10):
                self.logger.info("Too far out")
                return
        self.logger.info("All correct")
        self.submitter.increment_mark(1)
        self.ii.highz_pin(2)
        time.sleep(0.1)
        leds_after = self.ii.read_port(0)
        self.logger.info("After releasing SW2, LEDs returned to: {l:#x}".format(l = leds_after))
        if leds_before == leds_after:
            self.logger.info("Correctly restored")
            self.submitter.increment_mark(1)
        else:
            self.logger.critical("Did not correctly restore")
