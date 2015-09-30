import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError
import interrogator_interface
import gdb_interface

class PracExam0Tests(PracTests):
    def build(self):
        self.clean_marker_directory()
        os.chdir('/home/marker/')
        for f in self.submitter.files:
            escaped_dir = self.submitter.submission_directory.replace("'", "\\'")
            cmd = "cp \"{d}/{f}\" /home/marker/".format(d = escaped_dir, f = f)
            self.exec_as_marker(cmd)
        all_files = os.listdir()
        s_files = [fi for fi in all_files if fi.endswith(".s")]
        self.logger.info("Found {n} .s files.".format(n = len(s_files)))
        for s_file in s_files:
            cmd = "sed -i \"s/.word 0xCA71D738/.word 0xCCEE2244/g\" {f}".format(f = s_file)
            self.exec_as_marker(cmd)
        self.logger.info("Your source file has been modified to replace .word 0xCA71D7398 with .word 0xCCEE2244")
        self.logger.info("The highest byte in the block is now 0xEE")
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
            self.logger.info("----------- PART 4 ----------------")
            self.part_4_tests()
            self.logger.info("----------- PART 5 ----------------")
            self.part_5_tests()
            self.logger.info("----------- PART 6 ----------------")
            self.part_6_tests()
        except TestFailedError as e:
            self.logger.critical("A test failed. Marking cannot continue")
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
        except gdb_interface.GDBException as e:
            self.logger.critical("Your program did not respond the way GDB expected it to")

    def part_1_tests(self):
        self.gdb.run_to_label('copy_to_RAM_complete')
        data = [0xA5588A12, 0x67BA553D, 0xCDEF2345, 0x35CDEC45]
        base_addr = 0x20000000
        for idx, word in enumerate(data):
            found = self.gdb.read_word(base_addr + (4*idx))
            self.logger.info("At RAM offset {offset}, expected {expected:#x}, found {found:#x}".format(
                offset = idx, expected = data[idx], found = found))
            if found != data[idx]:
                self.logger.critical("Wrong.")
                return
        self.logger.info("All correct.")
        self.submitter.increment_mark(2)

    def part_2_tests(self):
        self.logger.info("Checking case for largest element not the last element")
        self.gdb.run_to_label('display_maximum_done')
        leds = self.ii.read_port(0)
        self.max_displayed = leds
        self.logger.info("On LEDs, expected 0xef, found {leds:#x}".format(leds = leds))
        if leds != 0xef:
            self.logger.critical("Wrong")
            return
        self.submitter.increment_mark(2)
        self.logger.info("Now trying case where best element is the last one")
        self.gdb.soft_reset()
        self.gdb.run_to_label('copy_to_RAM_complete')
        self.gdb.write_word(0x2000000C, 0xF4CCEF34)
        self.logger.info("Set contents of address 0x2000000C to value 0xF4CCEF34")
        self.gdb.run_to_label('display_maximum_done')
        leds = self.ii.read_port(0)
        self.max_displayed = leds
        self.logger.info("On LEDs, expected 0xf4, found {leds:#x}".format(leds = leds))
        if leds != 0xf4:
            self.logger.critical("Wrong")
            return
        self.submitter.increment_mark(1)


    def part_3_tests(self):
        self.gdb.run_to_label('main_loop')
        self.logger.info("Checking that the timer is running and generating interrupts")
        tim6_isr_addr = self.gdb.read_word(0x08000000 + 0x84)
        try:
            self.gdb.run_to_address(tim6_isr_addr & 0xFFFFFFFE)
        except Exception as e:
            self.logger.exception(e)
            self.logger.critical("TIM6 does not seem to be running. Exiting tests")
            return
        time.sleep(0.1)
        self.gdb.send_control_c()
        first_cnt = self.gdb.read_word(0x40001000 + 0x24)
        time.sleep(0.1)
        self.gdb.send_control_c()
        second_cnt = self.gdb.read_word(0x40001000 + 0x24)
        if first_cnt == second_cnt:
            self.logger.critical("TIM6 does not seem to be running. Leaving test")
            return
        self.logger.info("TIM6 seems to be running. Now checking timing")
        leds = self.ii.read_port(0)
        self.gdb.send_continue()
        try:
            self.logger.info("Looking for transition: {a:#x} -> {b:#x}".format(a = leds+1, b = leds+2))
            timing = round(self.ii.timing_transition(leds+1, leds+2), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("Could not find incrementing transition")
            return
        self.logger.info("Found transition. Timing should be 1.5 second. Found to be: {t} second".format(t = timing))
        if (timing > 1.5*0.95 and timing < 1.5*1.05):
            self.logger.info("Correct.")
            self.submitter.increment_mark(1)
        else:
            self.logger.critical("Too far out. Not awarding marks")
            return

    def part_4_tests(self):
        t0 = time.time()
        self.logger.info("Trying to find transition from 0xF8 to another value.")
        self.logger.info("Waiting a maximum of 20 seconds for 0xF8")
        while(True):
            time.sleep(0.1)
            if (self.ii.read_port(0) == 0xF8):
                break
            if (time.time() - t0 > 20):
                self.logger.critical("Could not find 0xF8 in 20 seconds. Aborting")
                return
        self.logger.info("Got 0xF8. Checking what's next")
        t0 = time.time()
        while(True):
            time.sleep(0.1)
            if (self.ii.read_port(0) != 0xF8):
                break
            if (time.time() - t0 > 5):
                self.logger.critical("Got stuck on 0xF8 for more than 5 seconds. Aborting")
                return
        leds = self.ii.read_port(0)
        self.logger.info("After 0xF8, LEDs went to: {leds:#x}".format(leds = leds))
        if leds in [0xF4, 0xEF]:
            self.logger.info("Correct")
            self.submitter.increment_mark(2)
        else:
            self.logger.critical("Wrong")

    def part_5_tests(self):
        self.logger.info("Asserting SW1 and then immediately sampling the LEDs")
        self.ii.clear_pin(1)
        time.sleep(0.005)
        leds = self.ii.read_port(0)
        self.logger.info("LEDs found to show: {leds:#x}".format(leds = leds))
        if (leds != 0xEF) and (leds != 0xF4):
            self.logger.critical("Maximum not displayed.")
            return
        self.logger.info("Sleeping for a bit to see that the value stays there")
        time.sleep(3)
        leds_new = self.ii.read_port(0)
        self.logger.info("LEDs now found to show: {leds:#x}".format(leds = leds_new))
        if leds != leds_new:
            self.logger.info("They changed. Wrong")
            return
        self.logger.info("Good. Now checking that they return to incrementing when released")
        self.ii.highz_pin(1)
        self.logger.info("Looking for: {a:#x} -> {b:#x}".format(a = leds_new+1, b = leds_new+2))
        try:
            timing = round(self.ii.timing_transition(leds_new+1, leds_new+2), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("Could not find incrementing transition")
            return
        self.logger.info("Found transition. Found to be: {t} second".format(t = timing))
        self.submitter.increment_mark(1)

    def part_6_tests(self):
        leds_backup = self.ii.read_port(0)
        self.ii.highz_pin(1)
        self.ii.clear_pin(2)
        self.logger.info("Before holding SW2, LEDs showing: {leds:#x}".format(leds = leds_backup))
        self.ii.write_dac(1, 0x40)
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("For input of 0x40, LEDs showed: {leds:#x}".format(leds = leds))
        if (leds > 0x48) or (leds < 0x37):
            self.logger.critical("Wrong.")
            return
        self.ii.write_dac(1, 0x78)
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("For input of 0x78, LEDs showed: {leds:#x}".format(leds = leds))
        if (leds > 0x80) or (leds < 0x70):
            self.logger.critical("Wrong.")
            return
        self.ii.write_dac(1, 0xCC)
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("For input of 0xCC, LEDs showed: {leds:#x}".format(leds = leds))
        if (leds > 0xD5) or (leds < 0xC4):
            self.logger.critical("Wrong.")
            return
        self.logger.info("Good, now checking that LEDs restore when SW2 released")
        self.ii.highz_pin(2)
        time.sleep(0.05)
        leds_new = self.ii.read_port(0)
        self.logger.info("Backed up LEDs: {old:#x}. Restored LEDs: {new:#x}".format(old = leds_backup, new = leds_new))
        if (leds_backup != leds_new):
            self.logger.critical("Wrong")
            return
        self.submitter.increment_mark(1)
