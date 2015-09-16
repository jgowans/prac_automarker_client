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
        for f in self.group.files:
            cmd = "cp \"{d}/{f}\" /home/marker/".format(d = self.group.submission_directory, f = f)
            self.exec_as_marker(cmd)
        all_files = os.listdir()
        s_files = [fi for fi in all_files if fi.endswith(".s")]
        self.logger.info("Found {n} .s files.".format(n = len(s_files)))
        cmd = "sed -i \"s/.word 0x34CCEB44/.word 0xE1CC2244/g\" {f}".format(f = s_files[0])
        self.exec_as_marker(cmd)
        self.logger.info("Your source file has been modified to replace .word 0x34CCEB44 with .word 0xE1CC2244")
        self.logger.info("The highest byte in the block is not 0xE1")
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
        self.gdb.run_to_label('copy_to_RAM_complete')
        data = [0xA4578911, 0x66B9543C, 0xCA71D738, 0xE1CC2244]
        base_addr = 0x20000000
        for idx, word in enumerate(data):
            found = self.gdb.read_word(base_addr + (4*idx))
            self.logger.info("At RAM offset {offset}, expected {expected:#x}, found {found:#x}".format(
                offset = idx, expected = data[idx], found = found))
            if found != data[idx]:
                self.logger.critical("Wrong.")
                return
        self.logger.info("All correct.")
        self.student.increment_mark(2)

    def part_2_tests(self):
        self.logger.info("Checking case for largest element not the last element")
        self.gdb.run_to_label('display_maximum_done')
        leds = self.ii.read_port(0)
        self.max_displayed = leds
        self.logger.info("On LEDs, expected 0xe2, found {led}".format(leds = leds))
        if leds != 0xe2:
            self.logger.critical("Wrong")
            return
        self.student.increment_mark(2)
        self.logger.info("Now trying case where best element is the last one")
        self.gdb.soft_reset()
        self.gdb.run_to_label('copy_to_RAM_complete')
        self.gdb.write_word(0x20000000 + 4*3, 0x34CCE0F4)
        self.logger.info("Set contents of address 0x20000000 + 4*3 to value 0x34CCE0F4")
        self.gdb.run_to_label('display_maximum_done')
        leds = self.ii.read_port(0)
        self.max_displayed = leds
        self.logger.info("On LEDs, expected 0xf4, found {led}".format(leds = leds))
        if leds != 0xf4
            self.logger.critical("Wrong")
            return
        self.student.increment_mark(1)


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
            return
        self.logger.info("TIM6 seems to be running. Now checking timing")
        leds = self.ii.read_port(0)
        self.gdb.send_continue()
        try:
            timing = round(self.ii.timing_transition(leds+1, leds+2), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("Could not find incrementing transition")
            return
        self.logger.info("Found transition. Timing should be 1.5 second. Found to be: {t} second".format(t = timing))
        if (timing > 1.5*0.95 and timing < 1.5*1.05):
            self.logger.info("Correct.")
            self.student.increment_mark(1)
        else:
            self.logger.critical("Too far out. Not awarding marks")
            return

    def part_4_tests(self):
        self.gdb.send_control_c()
        self.gdb.run_to_label('main_loop')
        current_leds = self.gdb.read_word(0x48000400 + 0x14)
        new_leds = (current_leds & ~(0xFF)) | 0xF6
        self.gdb.write_word(0x48000400 + 0x14, new_leds)
        self.logger.info("Forcing LEDs to 0xF6")
        if self.max_displayed == 0xf4:
            self.logger.info("Trying to find transition from 0xF8 to 0xF4")
            self.gdb.send_continue()
            try:
                timing = round(self.ii.timing_transition(0xF8, 0xF4), 2)
            except interrogator_interface.LEDTimingTimeout as e:
                self.logger.critical("Could not find incrementing transition")
                return
            self.logger.info("Found transition. Timing should be 1.5 second. Found to be: {t} second".format(t = timing))
            if (timing > 1.5*0.95 and timing < 1.5*1.05):
                self.logger.info("Correct.")
                self.student.increment_mark(2)
            else:
                self.logger.critical("Too far out. Not awarding marks")
                return
        elif self.max_displayed == 0xE0:
            self.logger.info("Part 2 didn't quite work. You seemed to find a max of 0xE0. Looking for that")
            self.logger.info("Trying to find transition from 0xF8 to 0xE0")
            self.gdb.send_continue()
            try:
                timing = round(self.ii.timing_transition(0xF8, 0xE0), 2)
            except interrogator_interface.LEDTimingTimeout as e:
                self.logger.critical("Could not find incrementing transition")
                return
            self.logger.info("Found transition. Timing should be 1.5 second. Found to be: {t} second".format(t = timing))
            if (timing > 1.5*0.95 and timing < 1.5*1.05):
                self.logger.info("Correct.")
                self.student.increment_mark(2)
            else:
                self.logger.critical("Too far out. Not awarding marks")
                return
        else:
            self.logger.warning("Part 2 didn't work, so I'm not sure what maximum to look for.")
            self.logger.info("First trying what you displayed: {m:#x}".format(m = self.max_displayed))
            self.gdb.send_continue()
            try:
                timing = round(self.ii.timing_transition(0xF8, self.max_displayed), 2)
                self.logger.info("Found transition. Timing should be 1.5 second. Found to be: {t} second".format(t = timing))
                if (timing > 1.5*0.95 and timing < 1.5*1.05):
                    self.logger.info("Correct.")
                    self.student.increment_mark(2)
                else:
                    self.logger.critical("Too far out. Not awarding marks")
                    return
            except interrogator_interface.LEDTimingTimeout as e:
                self.logger.critical("Could not find incrementing transition")
            self.logger.info("That didn't work... Trying to look for actual maximum: 0xF4")
            self.gdb.send_control_c()
            self.gdb.run_to_label('main_loop')
            current_leds = self.gdb.read_word(0x48000400 + 0x14)
            new_leds = (current_leds & ~(0xFF)) | 0xF6
            self.gdb.write_word(0x48000400 + 0x14, new_leds)
            self.logger.info("Forcing LEDs to 0xF6")
            try:
                timing = round(self.ii.timing_transition(0xF8, 0xF4), 2)
            except interrogator_interface.LEDTimingTimeout as e:
                self.logger.critical("Could not find incrementing transition")
                return
            self.logger.info("Found transition. Timing should be 1.5 second. Found to be: {t} second".format(t = timing))
            if (timing > 1.5*0.95 and timing < 1.5*1.05):
                self.logger.info("Correct.")
                self.student.increment_mark(2)
            else:
                self.logger.critical("Too far out. Not awarding marks")
                return

    def part_4_tests(self):
        self.logger.info("Asserting SW1 and then immediately sampling the LEDs")
        self.ii.clear_pin(1)
        time.sleep(0.005)
        leds = self.ii.read_port(0)
        self.logger.info("LEDs found to show: {leds:#x}".format(leds = leds))
        if (leds != 0xE2) and (leds != 0xE0) and (leds != 0xF4):
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
        self.logger.info("Looking for: {a:#x} -> {b:#x}".format(a = leds_new+2, b = leds_new+3))
        self.gdb.send_continue()
        try:
            timing = round(self.ii.timing_transition(leds_new+2, leds_new+3), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("Could not find incrementing transition")
            return
        self.logger.info("Found transition. Timing should be 1.5 second. Found to be: {t} second".format(t = timing))
        if (timing > 1.5*0.95 and timing < 1.5*1.05):
            self.logger.info("Correct.")
            self.student.increment_mark(1)
        else:
            self.logger.critical("Too far out. Not awarding marks")
            return

    def part_5_tests(self):
        leds_backup = self.ii.read_port(0)
        self.ii.clear_pin(2)
        self.logger.info("Before holding SW2, LEDs showing: {leds}".format(leds = leds))
        self.ii.write_dac(1, 0x40)
        time.sleep(0.1)
        leds = ii.read_port(0)
        self.logger.info("For input of 0x40, LEDs showed: {leds}".format(leds = leds))
        if (leds > 0x48) or (leds < 0x37):
            self.logger.critical("Wrong.")
            return
        self.ii.write_dac(1, 0x78)
        time.sleep(0.1)
        leds = ii.read_port(0)
        self.logger.info("For input of 0x78, LEDs showed: {leds}".format(leds = leds))
        if (leds > 0x80) or (leds < 0x70):
            self.logger.critical("Wrong.")
            return
        self.ii.write_dac(1, 0xCC)
        time.sleep(0.1)
        leds = ii.read_port(0)
        self.logger.info("For input of 0xCC, LEDs showed: {leds}".format(leds = leds))
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
        self.student.increment_mark(1)

