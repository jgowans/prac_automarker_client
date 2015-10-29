import elf_parser
import time, os
import subprocess
from prac_tests import PracTests, TestFailedError, BuildFailedError, SourceFileProblem
import interrogator_interface
import gdb_interface
import zipfile

class Prac8Tests(PracTests):
    def catalogue_submission_files(self):
        os.chdir(self.submitter.submission_directory)
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
        try:
            self.logger.info("----------- PART 1 ----------------")
            self.part_1_tests()
        except TestFailedError as e:
            self.logger.critical("A test failed. Marking cannot continue")
        except interrogator_interface.LEDTimingTimeout as e:
            self.logger.critical("LEDs timing checker timed out before finding expected patterns")
        except gdb_interface.GDBException as e:
            self.logger.critical("Your program did not respond the way GDB expected it to")

    def part_1_tests(self):
        self.gdb.run_to_function('main')
        array_addr = self.gdb.get_variable_value('&(array[0])')
        try:
            smaller_ptr_addr = self.gdb.get_variable_value('&closest_pair_smaller_ptr')
        except:
            smaller_ptr_addr = self.gdb.get_variable_value('&closest_pair_smaller')
        try:
            larger_ptr_addr = self.gdb.get_variable_value('&closest_pair_larger_ptr')
        except:
            larger_ptr_addr = self.gdb.get_variable_value('&closest_pair_larger')
        self.gdb.run_to_function('find_closest_pair')
        self.logger.info('Modifying smaller and larger pointer to both point to NULL')
        self.gdb.set_variable_value('*(uint16_t **){a:#x}'.format(a = smaller_ptr_addr), 0)
        self.gdb.set_variable_value('*(uint16_t **){a:#x}'.format(a = larger_ptr_addr), 0)
        self.logger.info('Modifying array[4] to have the value 401')
        self.gdb.set_variable_value('*(((uint16_t*){a:#x}) + 4)'.format(a = array_addr), 401)
        self.gdb.send_finish()
        self.logger.info("Allowing function to run until it returns")
        try:
            smaller_ptr_val = self.gdb.get_variable_value('closest_pair_smaller_ptr')
        except:
            smaller_ptr_val = self.gdb.get_variable_value('closest_pair_smaller')
        try:
            larger_ptr_val = self.gdb.get_variable_value('closest_pair_larger_ptr')
        except:
            larger_ptr_val = self.gdb.get_variable_value('closest_pair_larger')
        self.logger.info("Smaller pointer should point to: {a:#x} + (2*3) = {b:#x}".format(
            a = array_addr, b = array_addr + (2*3)))
        self.logger.info("Smaller pointer found pointing to: {a:#x}".format(a = smaller_ptr_val))
        self.logger.info("Larger pointer should point to {a:#x} + (2*4) = {b:#x}".format(
            a = array_addr, b = array_addr + (2*4)))
        self.logger.info("Larger pointer found pointing to: {a:#x}".format(a = larger_ptr_val))
        if (smaller_ptr_val != array_addr + 2*3) or (larger_ptr_val != array_addr + 2*4):
            self.logger.critical("Incorrect")
            return
        self.logger.info("Correct!")
        self.submitter.increment_mark(1)
        self.logger.info("Now trying case where best pair is last pair")
        self.gdb.soft_reset()
        self.gdb.run_to_function('find_closest_pair')
        self.logger.info('Modifying smaller and larger pointer to both point to NULL')
        self.gdb.set_variable_value('*(uint16_t **){a:#x}'.format(a = smaller_ptr_addr), 0)
        self.gdb.set_variable_value('*(uint16_t **){a:#x}'.format(a = larger_ptr_addr), 0)
        self.logger.info('Modifying array[7] to have the value 1500')
        self.gdb.set_variable_value('*(((uint16_t*){a:#x}) + 7)'.format(a = array_addr), 1500)
        self.logger.info('Modifying array[9] to have the value 2100')
        self.gdb.set_variable_value('*(((uint16_t*){a:#x}) + 9)'.format(a = array_addr), 2100)
        self.gdb.send_finish()
        self.logger.info("Allowing function to run until it returns")
        try:
            smaller_ptr_val = self.gdb.get_variable_value('closest_pair_smaller_ptr')
        except:
            smaller_ptr_val = self.gdb.get_variable_value('closest_pair_smaller')
        try:
            larger_ptr_val = self.gdb.get_variable_value('closest_pair_larger_ptr')
        except:
            larger_ptr_val = self.gdb.get_variable_value('closest_pair_larger')
        self.logger.info("Smaller pointer should point to: {a:#x} + (2*8) = {b:#x}".format(
            a = array_addr, b = array_addr + (2*8)))
        self.logger.info("Smaller pointer found pointing to: {a:#x}".format(a = smaller_ptr_val))
        self.logger.info("Larger pointer should point to {a:#x} + (2*9) = {b:#x}".format(
            a = array_addr, b = array_addr + (2*9)))
        self.logger.info("Larger pointer found pointing to: {a:#x}".format(a = larger_ptr_val))
        if (smaller_ptr_val != array_addr + 2*8) or (larger_ptr_val != array_addr + 2*9):
            self.logger.critical("Incorrect")
            return
        self.logger.info("Correct!")
        self.submitter.increment_mark(1)
        self.logger.info("Now trying case where best pair is first pair")
        self.gdb.soft_reset()
        self.gdb.run_to_function('find_closest_pair')
        self.logger.info('Modifying smaller and larger pointer to both point to NULL')
        self.gdb.set_variable_value('*(uint16_t **){a:#x}'.format(a = smaller_ptr_addr), 0)
        self.gdb.set_variable_value('*(uint16_t **){a:#x}'.format(a = larger_ptr_addr), 0)
        self.logger.info('Modifying array[0] to have the value 222')
        self.gdb.set_variable_value('*(((uint16_t*){a:#x}) + 0)'.format(a = array_addr), 222)
        self.gdb.send_finish()
        self.logger.info("Allowing function to run until it returns")
        try:
            smaller_ptr_val = self.gdb.get_variable_value('closest_pair_smaller_ptr')
        except:
            smaller_ptr_val = self.gdb.get_variable_value('closest_pair_smaller')
        try:
            larger_ptr_val = self.gdb.get_variable_value('closest_pair_larger_ptr')
        except:
            larger_ptr_val = self.gdb.get_variable_value('closest_pair_larger')
        self.logger.info("Smaller pointer should point to: {a:#x} + (2*0) = {b:#x}".format(
            a = array_addr, b = array_addr + (2*0)))
        self.logger.info("Smaller pointer found pointing to: {a:#x}".format(a = smaller_ptr_val))
        self.logger.info("Larger pointer should point to {a:#x} + (2*1) = {b:#x}".format(
            a = array_addr, b = array_addr + (2*1)))
        self.logger.info("Larger pointer found pointing to: {a:#x}".format(a = larger_ptr_val))
        if (smaller_ptr_val != array_addr + 2*0) or (larger_ptr_val != array_addr + 2*1):
            self.logger.critical("Incorrect")
            return
        self.logger.info("Correct!")
        self.submitter.increment_mark(2)
        self.logger.info("Checking that code compiles with no warnings")
        cmd = "arm-none-eabi-gcc -g -Wall -Werror -mthumb -mcpu=cortex-m0 -S -o foo.s {src}".format(src = self.submitter.sourcefiles[0])
        try:
            self.exec_as_marker(cmd)
            self.logger.info("Correct. All the marks for you")
        except:
            self.logger.critical("Did not compile without warnings.")
            self.logger.critical("Mark set to 50%")
            self.submitter.mark = 2
