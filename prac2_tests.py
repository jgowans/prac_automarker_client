import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError
import interrogator_interface
import gdb_interface

class Prac2Tests(PracTests):
    def build(self):
        os.chdir(self.group.submission_directory)
        try:
            assembler_cmdline = ['arm-none-eabi-as',
                                 '-g',
                                 '-mthumb', 
                                 '-mcpu=cortex-m0',
                                 '-o', 'main.o',
                                 '{s}'.format(s = self.group.src_file)]
            subprocess.check_output(
                assembler_cmdline, 
                stderr=subprocess.STDOUT)
            self.logger.info("Assembler ran successfully")
            linker_cmdline = ['arm-none-eabi-ld',
                              '-Ttext=0x08000000',
                              '-o', 'main.elf',
                              'main.o']
            subprocess.check_output(
                linker_cmdline, 
                stderr=subprocess.STDOUT)
            self.logger.info("Linker process ran successfully")
        except subprocess.CalledProcessError as e:
            self.logger.info("Received build error: \n{err}".format(err = e.output))
            raise BuildFailedError

    def run_specific_prac_tests(self):
        self.gdb.open_file('main.elf')
        self.gdb.connect()
        self.gdb.erase()
        self.gdb.load()
        self.gdb.send_continue()
        self.ii.highz_pin(0)
        self.ii.highz_pin(1)
        self.ii.highz_pin(2)
        self.ii.highz_pin(3)
        self.ii.write_dac(0xFF)
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
            self.logger.info("------------ BONUS ----------------")
            self.bonus_tests()
        except TestFailedError as e:
            self.logger.critical("A test failed. Marking cannot continue")
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
        except gdb_interface.GDBException as e:
            self.logger.critical("Your program did not respond the way GDB expected it to")


    def assert_led_value(self, val):
        leds = self.ii.read_port(0)
        self.logger.info("LEDs should read {v:#x}. Found to be: {l:#x}".format(v = val, l = leds))
        if leds == val:
            return True
        else:
            raise TestFailedError

    def part_1_tests(self):
        time.sleep(1)
        leds = self.ii.read_port(0)
        self.logger.info("Value on LEDs: {v:#x}".format(v = leds))
        self.logger.info("Checking timing for pattern transition: {p0:#X}->{p1:#X}".format(p0 = leds+2, p1 = leds+3))
        timing = round(self.ii.timing_transition(leds+2, leds+3), 2)
        self.logger.info("Timing should be between 0.67 and 0.73 seconds. Found to be {t} seconds.".format(t=timing))
        if (timing >= 0.67) and (timing <= 0.73):
            self.group.mark += 2
            self.logger.info("Mark set to {m}".format(m = self.group.mark))
        else:
            self.logger.critical("Wrong. Exiting tests")
            raise TestFailedError

    def part_2_tests(self):
        self.ii.clear_pin(0)
        self.logger.info("Holding down SW0")
        time.sleep(1)
        leds = self.ii.read_port(0)
        self.logger.info("Value on LEDs: {v:#x}".format(v = leds))
        self.logger.info("Checking timing for pattern transition: {p0:#X}->{p1:#X}".format(p0 = leds+4, p1 = leds+6))
        timing = round(self.ii.timing_transition(leds+4, leds+6), 2)
        self.logger.info("Timing should be between 0.67 and 0.73 seconds. Found to be {t} seconds.".format(t=timing))
        if (timing >= 0.67) and (timing <= 0.73):
            self.group.mark += 2
            self.logger.info("Mark set to {m}".format(m = self.group.mark))
        else:
            self.logger.critical("Wrong. Exiting tests")
            raise TestFailedError

    def part_3_tests(self):
        self.ii.clear_pin(0)
        self.ii.clear_pin(1)
        self.logger.info("Holding down SW0 and SW1")
        time.sleep(1)
        leds = self.ii.read_port(0)
        self.logger.info("Value on LEDs: {v:#x}".format(v = leds))
        self.logger.info("Checking timing for pattern transition: {p0:#X}->{p1:#X}".format(p0 = leds+4, p1 = leds+6))
        timing = round(self.ii.timing_transition(leds+4, leds+6), 2)
        self.logger.info("Timing should be between 0.27 and 0.33 seconds. Found to be {t} seconds.".format(t=timing))
        if (timing >= 0.27) and (timing <= 0.33):
            self.group.mark += 2
            self.logger.info("Mark set to {m}".format(m = self.group.mark))
        else:
            self.logger.critical("Wrong. Exiting tests")
            raise TestFailedError

    def part_4_tests(self):
        self.logger.info("Releasing SW0 and SW1")
        self.ii.highz_pin(0)
        self.ii.highz_pin(1)
        self.logger.info("Holding SW2")
        self.ii.clear_pin(2)
        time.sleep(1)
        self.assert_led_value(0xAA)
        time.sleep(3)
        self.assert_led_value(0xAA)
        self.logger.info("Releasing SW2")
        self.ii.highz_pin(2)
        leds = self.ii.read_port(0)
        self.logger.info("Checking timing for pattern transition: {p0:#X}->{p1:#X}".format(p0 = 0xAB, p1 = 0xAC))
        timing = round(self.ii.timing_transition(0xAB, 0xAC), 2)
        self.logger.info("Timing should be between 0.67 and 0.73 seconds. Found to be {t} seconds.".format(t=timing))
        if (timing >= 0.67) and (timing <= 0.73):
            self.group.mark += 1
            self.logger.info("Mark set to {m}".format(m = self.group.mark))
        else:
            self.logger.critical("Wrong. Exiting tests")
            raise TestFailedError

    def part_5_tests(self):
        self.logger.info("Holding SW3")
        self.ii.clear_pin(3)
        time.sleep(1)
        before = self.ii.read_port(0)
        self.logger.info("Sleeping for 5 seconds")
        time.sleep(5)
        after = self.ii.read_port(0)
        self.logger.info("Before sleep, leds = {b:#x}. After sleep, leds = {a:#x}".format(b = before, a = after))
        if before != after:
            self.logger.critical("Wrong. Exiting tests")
            raise TestFailedError
        self.logger.info("Releasing SW3")
        self.ii.highz_pin(3)
        leds = self.ii.read_port(0)
        self.logger.info("Value on LEDs: {v:#x}".format(v = leds))
        self.logger.info("Checking timing for pattern transition: {p0:#X}->{p1:#X}".format(p0 = leds+2, p1 = leds+3))
        timing = round(self.ii.timing_transition(leds+2, leds+3), 2)
        self.logger.info("Timing should be between 0.67 and 0.73 seconds. Found to be {t} seconds.".format(t=timing))
        if (timing >= 0.67) and (timing <= 0.73):
            self.group.mark += 1
            self.logger.info("Mark set to {m}".format(m = self.group.mark))
        else:
            self.logger.critical("Wrong. Exiting tests")
            raise TestFailedError

    def bonus_tests(self):
        self.ii.clear_pin(1)
        self.logger.info("Holding down SW1")
        try:
            self.gdb.send_control_c()
            self.gdb.soft_reset()
            self.ii.write_dac(0)
            self.logger.info("Pot set to 0V, expect 0.05 timing")
            self.gdb.send_continue()
            timing = round(self.ii.timing_transition(20, 21), 2)
            self.logger.info("Timing found to be {t} seconds.".format(t=timing))
            if (timing >= 0.04) and (timing <= 0.06):
                pass
            else:
                raise TestFailedError
            self.gdb.send_control_c()
            self.gdb.soft_reset()
            self.ii.write_dac(77)
            time.sleep(1)
            self.logger.info("Pot set to 1V, expect 0.13 timing")
            self.gdb.send_continue()
            timing = round(self.ii.timing_transition(10, 11), 2)
            self.logger.info("Timing found to be {t} seconds.".format(t=timing))
            if (timing >= 0.11) and (timing <= 0.15):
                pass
            else:
                raise TestFailedError
            self.gdb.send_control_c()
            self.gdb.soft_reset()
            self.ii.write_dac(155)
            time.sleep(1)
            self.logger.info("Pot set to 2V, expect 0.20 timing")
            self.gdb.send_continue()
            timing = round(self.ii.timing_transition(5, 6), 2)
            self.logger.info("Timing found to be {t} seconds.".format(t=timing))
            if (timing >= 0.18) and (timing <= 0.22):
                pass
            else:
                raise TestFailedError
            self.group.mark += 1
            self.logger.info("Mark set to {m}".format(m = self.group.mark))
        except TestFailedError as e:
            pass
        except interrogator_interface.LEDTimingTimeout  as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
