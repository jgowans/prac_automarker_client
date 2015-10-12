import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError, SourceFileProblem
import interrogator_interface
import gdb_interface
import zipfile

class Prac7Tests(PracTests):
    def catalogue_submission_files(self):
        os.chdir(self.submitter.submission_directory)
        all_files = os.listdir()
        self.logger.info("Before unzip, directory contains: {f}".format(f = all_files))
        zip_files = [fi for fi in all_files if fi.endswith(".zip")]
        if len(zip_files) != 1:
            self.logger.critical("Too many or not enough zip files found out of: {a}. Aborting.".format(a = all_files))
            raise SourceFileProblem
        self.logger.info("Extracting zipfile: {z}".format(z = zip_files[0]))
        try:
            with zipfile.ZipFile(zip_files[0]) as z:
                    z.extractall()
        except zipfile.BadZipFile as e:
            self.logger.critical(str(e))
            raise BuildFailedError
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
        self.gdb.soft_reset()
        self.gdb.erase()
        self.gdb.soft_reset()
        try:
            self.gdb.load()
        except gdb_interface.CodeLoadFailed as e:
            return
        try:
            self.gdb.verify()
        except gdb_interface.CodeVerifyFailed as e:
            return
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
            #self.logger.info("----------- BONUS ----------------")
            #self.bonus_tests()
        except TestFailedError as e:
            self.logger.critical("A test failed. Marking cannot continue")
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
        except gdb_interface.GDBException as e:
            self.logger.critical("Your program did not respond the way GDB expected it to")
        self.ii.highz_pin(0)
        self.ii.highz_pin(1)
        self.ii.highz_pin(2)
        self.ii.highz_pin(3)
        self.ii.write_dac(0, 0)
        self.ii.write_dac(1, 0)

    def part_1_tests(self):
        self.gdb.send_continue()
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("Found on LEDs: {l:#x}".format(l = leds))
        if leds != 0xC0:
            self.logger.critical("Incorrect.")
            return
        time.sleep(3)
        leds = self.ii.read_port(0)
        if leds != 0xC0:
            self.logger.critical("After sleeping for 3 seconds:")
            self.logger.info("Found on LEDs: {l:#x}".format(l = leds))
            self.logger.critical("Incorrect.")
            return
        self.logger.info("Correct")
        self.logger.info("Holding SW0")
        self.ii.clear_pin(0)
        self.logger.info("Looking for transition {p0:#x} -> {p1:#x}".format(
            p0 = leds+2, p1 = leds+3))
        try:
            timing = round(self.ii.timing_transition(leds+2, leds+3), 2)
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("Could not find incrementing transition")
            return
        self.logger.info("Found transition. Timing should be 0.5 second. Found to be: {t} second".format(t = timing))
        if (timing > 0.5*0.95 and timing < 0.5*1.05):
            self.logger.info("Correct.")
            self.submitter.increment_mark(1)
        else:
            self.logger.critical("Too far out. Not awarding mark.")
        self.logger.info("Releasing SW0")
        self.ii.highz_pin(0)
        time.sleep(1)
        leds_before = self.ii.read_port(0)
        self.logger.info("Found on LEDs: {l:#x}".format(l = leds_before))
        self.logger.info("Sleeping for 3 seconds")
        time.sleep(3)
        leds_after = self.ii.read_port(0)
        self.logger.info("Found on LEDs: {l:#x}".format(l = leds_after))
        if leds_before != leds_after:
            self.logger.critical("After sleeping for 3 seconds pattern changed")
            self.logger.critical("Incorrect.")
            return
        self.submitter.increment_mark(1)

    def part_2_tests(self):
        self.ii.highz_pin(0)
        time.sleep(1)
        self.logger.info("Briefly pulsing SW1 for 100 ms")
        self.ii.clear_pin(1)
        time.sleep(0.1)
        self.ii.highz_pin(0)
        leds = self.ii.read_port(0)
        self.logger.info("Found on LEDs: {l:#x}".format(l = leds))
        if leds != 0xC0:
            self.logger.critical("Incorrect.")
            return
        self.submitter.increment_mark(1)

    def part_3_tests(self):
        self.ii.highz_pin(0)
        self.ii.highz_pin(1)
        self.logger.info("Holding SW2")
        self.ii.clear_pin(2)
        self.ii.write_dac(0, 0x40)
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("For POT0 value of 0x40, LEDs showed: {leds:#x}".format(leds = leds))
        if (leds > 0x40*1.1) or (leds < 0x40*0.9):
            self.logger.critical("Wrong.")
            return
        self.ii.write_dac(0, 0x78)
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("For POT0 value of 0x78, LEDs showed: {leds:#x}".format(leds = leds))
        if (leds > 0x78*1.1) or (leds < 0x78*0.9):
            self.logger.critical("Wrong.")
            return
        self.ii.write_dac(0, 0xCC)
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("For POT0 value of 0xCC, LEDs showed: {leds:#x}".format(leds = leds))
        if (leds > 0xCC*1.1) or (leds < 0xCC*0.9):
            self.logger.critical("Wrong.")
            return
        self.submitter.increment_mark(3)

    def part_4_tests(self):
        self.ii.highz_pin(0)
        self.ii.highz_pin(1)
        self.ii.highz_pin(2)
        self.logger.info("Holding SW3")
        self.ii.clear_pin(3)
        self.ii.write_dac(1, 0xFF - 0x40)
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("For POT1 value of 0xFF - 0x40, LEDs showed: {leds:#x}".format(leds = leds))
        if (leds > 0x40*1.1) or (leds < 0x40*0.9):
            self.logger.critical("Wrong.")
            return
        self.ii.write_dac(1, 0xFF - 0x78)
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("For POT1 value of 0xFF - 0x78, LEDs showed: {leds:#x}".format(leds = leds))
        if (leds > 0x78*1.1) or (leds < 0x78*0.9):
            self.logger.critical("Wrong.")
            return
        self.ii.write_dac(1, 0xFF - 0xCC)
        time.sleep(0.1)
        leds = self.ii.read_port(0)
        self.logger.info("For POT1 value of 0xFF - 0xCC, LEDs showed: {leds:#x}".format(leds = leds))
        if (leds > 0xCC*1.1) or (leds < 0xCC*0.9):
            self.logger.critical("Wrong.")
            return
        self.submitter.increment_mark(2)

    def bonus_tests(self):
        leds_before = self.ii.read_port(0)
        self.logger.info("Found on LEDs: {l:#x}".format(l = leds_before))
        self.logger.info("Resetting through NRST as preliminary test")
        self.ii.reset(0) # pull NRST low
        time.sleep(3)
        self.ii.reset(1) # pull NRST high
        time.sleep(1)
        leds_after = self.ii.read_port(0)
        self.logger.info("Found on LEDs: {l:#x}".format(l = leds_after))
        if leds_before != leds_after:
            return
        self.logger.info("Correct. Note to self: test bonus properly")
