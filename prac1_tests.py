import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError

class Prac1Tests(PracTests):
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
            raise e

    def run_specific_prac_tests(self):
        self.gdb.open_file('main.elf')
        self.gdb.connect()
        self.gdb.erase()
        self.gdb.load()
        self.ii.highz_pin(3)
        self.logger.info("----------- PART 1 ----------------")
        self.part_1_tests()
        self.logger.info("----------- PART 2 ----------------")
        self.part_2_tests()
        self.logger.info("----------- PART 3 ----------------")
        self.part_3_tests()
        self.logger.info("------------ BONUS ----------------")
        self.bonus_tests()

    def assert_led_value(self, val):
        leds = self.ii.read_port(0)
        self.logger.info("LEDs should read {v:#x}. Found to be: {l:#x}".format(v = val, l = leds))
        if leds == val:
            return True
        else:
            return False


    def part_1_tests(self):
        self.gdb.run_to_label('main_loop')
        if self.assert_led_value(10) == True:
            self.group.mark += 2
            self.logger.info("Mark set to: {m}".format(m=self.group.mark))
        else:
            self.logger.critical("Wrong. Exiting tests")
            raise TestFailedError

    def part_2_tests(self):
        for i in range(11, 21):
            self.gdb.run_to_label('main_loop')
            if self.assert_led_value(i) == False:
                self.logger.critical("Wrong")
                if i > 11:
                    self.group.mark += 1
                self.logger.info("Mark set to {m}".format(m = self.group.mark))
                self.logger.info("Exiting tests")
                raise TestFailedError
        self.group.mark += 2
        self.logger.info("Mark set to {m}".format(m = self.group.mark))

    def part_3_tests(self):
        self.gdb.run_to_label('main_loop')
        if self.assert_led_value(10) == False:
            self.logger.critical("LEDs did not wrap to 10")
            raise TestFailedError
        self.group.mark += 1
        self.logger.info("LED's wrapped to ten. Mark set to {m}".format(m = self.group.mark))
        self.gdb.run_to_label('main_loop')
        if self.assert_led_value(11) == False:
            self.logger.critical("Did not continue counting after wrapping")
            raise TestFailedError
        self.group.mark += 1
        self.logger.info("LEDs continued counting after wrapping. Mark set to {m}".format(m = self.group.mark))

    def bonus_tests(self):
        self.logger.info("Holding SW3")
        self.ii.clear_pin(3)
        self.gdb.run_to_label('main_loop')
        if self.assert_led_value(10) == False:
            return
        self.gdb.run_to_label('main_loop')
        if self.assert_led_value(20) == False:
            return
        self.logger.info("Releasing SW3. Should count forward.")
        self.ii.highz_pin(3)
        self.gdb.run_to_label('main_loop')
        if self.assert_led_value(10) == False:
            return
        self.group.mark += 1
        self.logger.info("Bonus correct. Mark: {m}".format(m = self.group.mark))
