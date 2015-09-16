import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError
import interrogator_interface
import gdb_interface

class Prac5Tests(PracTests):
    def build(self):
        self.clean_marker_directory()
        os.chdir('/home/marker/')
        for f in self.group.files:
            cmd = "cp \"{d}/{f}\" /home/marker/".format(d = self.group.submission_directory, f = f)
            self.exec_as_marker(cmd)
        all_files = os.listdir()
        s_files = [fi for fi in all_files if fi.endswith(".s")]
        if len(s_files) != 1:
            self.logger.critical("Too many or too few .s files found. Should be only 1 .s file. Actual directory contents: {af}".format(af = all_files))
            raise BuildFailedError
        self.logger.info("Found only 1 .s file. Good!")
        cmd = "sed -i \"s/.word 0xBBAA5500/.word 0x55443366/g\" {f}".format(f = s_files[0])
        self.exec_as_marker(cmd)
        self.logger.info("Your source file has been modified to replace .word 0xBBAA5500 with .word 0x55443366")
        cmd = "sed -i \"s/.word 0xFFEEDDCC/.word 0x8877DDCC/g\" {f}".format(f = s_files[0])
        self.exec_as_marker(cmd)
        self.logger.info("Your source file has been modified to replace .word 0xFFEEDDCC with .word 0x8877DDCC")
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
            self.logger.info("----------- PART 3 ----------------")
            self.part_3_tests()
        except TestFailedError as e:
            self.logger.critical("A test failed. Marking cannot continue")
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
        except gdb_interface.GDBException as e:
            self.logger.critical("Your program did not respond the way GDB expected it to")

    def part_1_tests(self):
        self.logger.info("Checking that the timer is running and generating interrupts")
        tim6_isr_addr = self.gdb.read_word(0x08000000 + 0x84)
        try:
            self.gdb.run_to_address(tim6_isr_addr & 0xFFFFFFFE)
        except Exception as e:
            self.logger.exception(e)
            self.logger.critical("TIM6 does not seem to be running. Exiting tests")
            raise TestFailedError
        self.gdb.send_continue()
        time.sleep(0.1)
        self.gdb.send_control_c()
        first_cnt = self.gdb.read_word(0x40001000 + 0x24)
        self.gdb.send_continue()
        time.sleep(0.1)
        self.gdb.send_control_c()
        second_cnt = self.gdb.read_word(0x40001000 + 0x24)
        if first_cnt == second_cnt:
            self.logger.critical("TIM6 does not seem to be running. Leaving test")
            raise TestFailedError
        self.logger.info("TIM6 seems to be running. Now checking timing")
        leds = self.ii.read_port(0)
        self.gdb.send_continue()
        try:
            timing = round(self.ii.timing_transition(leds+1, leds+2), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("Could not find incrementing transition")
            return
        self.logger.info("Found transition. Timing should be 1 second. Found to be: {t} second".format(t = timing))
        if (timing > 1*0.95 and timing < 1*1.05):
            self.logger.info("Correct.")
            self.group.increment_mark(2)
        else:
            self.logger.critical("Too far out. Not awarding marks")
            return

    def part_2_tests(self):
        self.ii.clear_pin(0)
        self.logger.info("Asserting SW0")
        time.sleep(3)
        leds = self.ii.read_port(0)
        time.sleep(1)
        try:
            timing = round(self.ii.timing_transition(leds+1, leds+2), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("Could not find incrementing transition")
            return
        self.logger.info("Found transition. Timing should be 2 second. Found to be: {t} second".format(t = timing))
        if (timing > 2*0.95 and timing < 2*1.05):
            self.logger.info("Correct.")
            self.group.increment_mark(1)
        else:
            self.logger.critical("Too far out. Not awarding marks")
            return
        self.ii.highz_pin(0)
        self.logger.info("Releasing SW0 to check that timing returns to normal")
        time.sleep(3)
        leds = self.ii.read_port(0)
        try:
            timing = round(self.ii.timing_transition(leds+1, leds+2), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("Could not find incrementing transition")
            return
        self.logger.info("Found transition. Timing should be 1 second. Found to be: {t} second".format(t = timing))
        if (timing > 1*0.95 and timing < 1*1.05):
            self.logger.info("Correct.")
            self.group.increment_mark(1)
        else:
            self.logger.critical("Too far out. Not awarding marks")

    def part_3_tests(self):
        self.gdb.send_control_c()
        self.gdb.soft_reset()
        self.ii.clear_pin(1)
        self.gdb.send_continue()
        patterns = [0x66, 0x33, 0x44, 0x55, 0xCC, 0xDD, 0x77, 0x88]
        t0 = time.time()
        while(True):
            if (self.ii.read_port(0) == patterns[0]):
                break
            if (time.time() - t0 > 10):
                self.logger.critical("Could not find starting pattern in sequence. Aborting")
                raise TestFailedError
        for lower_idx in range(1, 12, 2):
            p0 = patterns[lower_idx % len(patterns)]
            p1 = patterns[(lower_idx+1) % len(patterns)]
            self.logger.info("Looking for transition {p0:#x} -> {p1:#x}".format(p0 = p0, p1 = p1))
            try:
               timing = round(self.ii.timing_transition(p0, p1), 2)
            except interrogator_interface.LEDTimingTimeout as e:
                self.logger.critical("Did not find transition")
                raise TestFailedError
            self.logger.info("Found transition. Timing should be 1 second. Found to be: {t} second".format(t = timing))
            if (timing > 1*0.95 and timing < 1*1.05):
                pass
            else:
                self.logger.critical("Incorrect. Exiting tests")
                raise TestFailedError
        self.logger.info("Patterns were cycled though.")
        self.group.increment_mark(1)
        self.logger.info("Now testing that cycle speeds is dependant on SW0")
        self.ii.clear_pin(0)
        self.ii.clear_pin(1)
        self.logger.info("Asserting both SW0 and SW1")
        self.gdb.send_control_c()
        self.gdb.soft_reset()
        self.gdb.send_continue()
        patterns = [0x66, 0x33, 0x44, 0x55, 0xCC, 0xDD, 0x77, 0x88]
        t0 = time.time()
        while(True):
            if (self.ii.read_port(0) == patterns[0]):
                break
            if (time.time() - t0 > 20):
                self.logger.critical("Could not find starting pattern in sequence. Aborting")
                raise TestFailedError
        for lower_idx in range(2, 12, 2):
            p0 = patterns[lower_idx % len(patterns)]
            p1 = patterns[(lower_idx+1) % len(patterns)]
            self.logger.info("Looking for transition {p0:#x} -> {p1:#x}".format(p0 = p0, p1 = p1))
            try:
               timing = round(self.ii.timing_transition(p0, p1), 2)
            except interrogator_interface.LEDTimingTimeout as e:
                self.logger.critical("Did not find transition")
                raise TestFailedError
            self.logger.info("Found transition. Timing should be 2 second. Found to be: {t} second".format(t = timing))
            if (timing > 2*0.95 and timing < 2*1.05):
                pass
            else:
                self.logger.critical("Incorrect. Exiting tests")
                raise TestFailedError
        self.logger.info("Patterns were cycles through at the reduced speed")
        self.group.increment_mark(1)
        self.logger.info("Now testing that it returns to incrementing when SW1 released")
        self.gdb.send_control_c()
        self.ii.highz_pin(0)
        self.ii.highz_pin(1)
        leds = self.ii.read_port(0)
        self.gdb.send_continue()
        try:
            timing = round(self.ii.timing_transition(leds+2, leds+3), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("Could not find incrementing transition")
        self.logger.info("Found transition. Timing should be 1 second. Found to be: {t} second".format(t = timing))
        if (timing > 1*0.95 and timing < 1*1.05):
            self.logger.info("Correct.")
            self.group.increment_mark(1)
        else:
            self.logger.critical("Too far out. Not awarding marks")
