from interface_lib import InterrogatorInterface, OpenOCD
from gdb_lib import GDBInterface
import elf_parser
import shlex, subprocess
import time
import random
import os

initial_array = [252, 31, 205, 62, 211, 58, 157, 105, 250, 60, 37, 106, 150, 160, 97, 50, 140, 218, 38, 204, 192, 188, 75, 117, 111, 100, 116, 11, 46, 192, 174, 182, 253, 0, 44, 64, 250, 1, 137, 123]

class Prac8Tests:
    def __init__(self, comment, submission_dir, src_name):
        self.comment = comment
        self.src_name = src_name
        self.full_path_to_elf = None
        self.submission_dir = submission_dir

    def build(self):
        self.comment("Changing dir to submission dir")
        os.chdir(self.submission_dir)
        all_files = os.listdir()
        elf_files = [fi for fi in all_files if fi.endswith(".elf")]
        if len(elf_files) > 0:
            self.comment("Elf files exist before make run: {e}".format(e = all_files))
            self.comment("Aborting")
            return False
        self.comment("Running 'make'")
        make_proc = subprocess.Popen(["make"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            return_code = make_proc.wait(timeout = 5)
        except subprocess.TimeoutExpired:
            make_proc.kill()
            self.comment("Make did not complete after 5 seconds. Aborting")
            return False
        if (return_code != 0):
            error_message = make_proc.communicate()
            self.comment("Make failed. Awarding 0. Error message:")
            self.comment(error_message[0].decode())
            self.comment(error_message[1].decode())
            return False
        self.comment("Make succeeded. Attempting to link.")
        self.comment("Searching submission directory for .elf files")
        all_files = os.listdir()
        elf_files = [fi for fi in all_files if fi.endswith(".elf")]
        if len(elf_files) > 1:
            self.comment("Too many elf files out of {e}".format(e = all_files))
            return False
        if len(elf_files) == 0:
            self.comment("No elf files out of: {e}".format(e = all_files))
            return False
        self.comment("One elf file produced: {e}".format(e = elf_files[0]))
        self.full_path_to_elf = self.submission_dir + "/" + elf_files[0]
        return True

    def run_tests(self):
        mark = 0
        self.comment("Starting to run prac 8 tests")
        self.ii = InterrogatorInterface()
        self.comment(self.ii.comms_test())
        self.ii.reset(0) # pull line low. This does a reset
        with OpenOCD(self.comment) as self.openocd:
            time.sleep(0.2)
            self.ii.reset(1) # release line. Allows OpenOCD to establish connection to core.
            with GDBInterface(self.full_path_to_elf, self.comment) as self.gdb:
                self.gdb.open_file()
                self.gdb.connect()
                self.gdb.erase()
                self.gdb.load()
                self.gdb.run_to_function("main")

                for test in [self.part1_tests, self.part2_tests, self.part3_tests]:
                    mark += test()

                self.ii.highz_pin(0)
                self.ii.highz_pin(1)
                self.ii.highz_pin(2)
                self.ii.highz_pin(3)

        self.comment("All tests complete. Mark: {m}".format(m=mark))
        return mark

    def part1_tests(self):
        self.comment("=== Part 1 ===")
        # verify no global vars
        if len(self.gdb.get_all_global_variables()) > 0:
            self.comment("Global variables defined, but should not be")
            return 0
        # get address of array, min and max
        min_address = self.gdb.get_variable_value("&min")
        max_address = self.gdb.get_variable_value("&max")
        # run to find_min_max
        self.gdb.run_to_function("find_min_max")
        # verify contents of addresses
        self.comment("Verifying contexts of min, max and array")
        min_val = self.gdb.read_word(min_address)
        if min_val != 0xFC:
            self.comment("Data in main::min should be 0xFC and is {v}. Incorrect".format(v = min_val))
            return 0
        max_val = self.gdb.read_word(max_address)
        if max_val != 0xFC:
            self.comment("Data in main::max should be 0xFC and is {v}. Incorrect".format(v = max_val))
            return 0
        self.comment("Verifying that array initialised correctly")
        for idx, val in enumerate(initial_array):
            found = self.gdb.get_variable_value("array[{i}]".format(i = idx))
            if val != found:
                self.comment("Array element error at index {i}.".format(i = idx))
                self.comment("Element should be {exp:#x}. Found to be {act:#x}".format(exp = val, act = found))
                return 0
        return 2

    def part2_tests(self):
        self.comment("=== Part 2 ===")
        # get function prototype of find_min_max. Verify
        return 2

    def part3_tests(self):
        self.comment("=== Part 3 ===")
        # run to find_min_max
        # modify the array
        # allow find_min_max to finish
        # verify values of min (2) and max (1)
        return 3

    def part4_tests(self):
        self.comment("=== Part 4 ===")
        # continue
        # verify delay between expected patterns. 
        return 3

