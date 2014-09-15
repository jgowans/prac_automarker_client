from interface_lib import InterrogatorInterface, GDBInterface, OpenOCD
import shlex, subprocess
import time
import random

FIB_NUMBERS = [0x00000001, 0x00000001, 0x00000002, 0x00000003, 0x00000005, 0x00000008, 0x0000000D, 0x00000015, 0x00000022, \
               0x00000037, 0x00000059, 0x00000090, 0x000000E9, 0x00000179, 0x00000262, 0x000003DB, 0x0000063D, 0x00000A18, \
               0x00001055, 0x00001A6D, 0x00002AC2, 0x0000452F, 0x00006FF1, 0x0000B520, 0x00012511, 0x0001DA31, 0x0002FF42, \
               0x0004D973, 0x0007D8B5, 0x000CB228, 0x00148ADD, 0x00213D05, 0x0035C7E2, 0x005704E7, 0x008CCCC9, 0x00E3D1B0, \
               0x01709E79, 0x02547029, 0x03C50EA2, 0x06197ECB, 0x09DE8D6D, 0x0FF80C38, 0x19D699A5, 0x29CEA5DD, 0x43A53F82, \
               0x6D73E55F, 0xB11924E1]

SPECIAL_ADDRESS = 0x20000A00
ILLEGAL_ADDRESS = 0x1234ABC0

class Prac5Tests:
    def __init__(self, comment, submission_dir, src_name):
        self.comment = comment
        self.src_name = src_name
        self.full_path_to_elf = None
        self.submission_dir = submission_dir

    def build(self):
        as_proc = subprocess.Popen(["arm-none-eabi-as", \
                "-mcpu=cortex-m0", "-mthumb", "-g", \
                "-o", self.submission_dir + "/main.o", \
                self.submission_dir + "/" + self.src_name], \
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if (as_proc.wait() != 0):
            error_message = as_proc.communicate()
            self.comment("Compile failed. Awarding 0. Error message:")
            self.comment(error_message[0].decode())
            self.comment(error_message[1].decode())
            return False
        self.comment("Compile succeeded. Attempting to link.")
        ld_proc = subprocess.Popen(["arm-none-eabi-ld", \
                "-Ttext=0x08000000", \
                "-o", self.submission_dir + "/main.elf", \
                self.submission_dir + "/main.o"], \
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if (ld_proc.wait() != 0):
            error_message = ld_proc.communicate()
            self.comment("Link failed. Awarding 0. Error message:")
            self.comment(error_message[0].decode())
            self.comment(error_message[1].decode())
            return False
        self.full_path_to_elf = self.submission_dir + "/main.elf"
        self.comment("Link succeeded")
        return True

    def run_tests(self):
        mark = 0
        self.comment("Starting to run prac 5 tests")
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
                self.comment("=== Part 1 ===")
                mark += self.part1_tests()

                self.ii.highz_pin(0)
                self.ii.highz_pin(1)

        self.comment("All tests complete. Mark: {m}".format(m=mark))
        return mark

    def scale_mark(self):
        self.comment("Scaling PRAC5 mark by factor dependant on submission time")
        self.comment("No scale factor implemented for this prac.")
        return mark

    def part1_tests(self):
        # run to initialisations_complete 
        if self.gdb.run_to_label("initialisations_complete") == False:
            return 0
        # set start of ram to some sensible value
        self.comment("Setting 0x20000000 to {sa:#x}".format(sa = SPECIAL_ADDRESS))
        self.gdb.write_word(0x20000000, SPECIAL_ADDRESS)
        # run to fib_calc_complete and verify fibs
        if self.gdb.run_to_label("fib_calc_complete") == False:
            self.comment("Could not hit label 'fib_calc_complete'. Aborting")
            return 0
        self.comment("Verifying array of fib numbers")
        for idx, val in enumerate(FIB_NUMBERS):
            address = 0x20002000 - 0x4 - (4 * idx)
            if self.gdb.read_word(address) != val:
                self.comment("Words at address {addr} should be {exp} but is {act}".format(\
                        addr = address, exp = val, act = gdb.read_word(address)))
                self.comment("Aborting")
                return 0
        self.comment("Verification completed successfully. 2/2")
        return 2

    def part2_tests(self):
        # run to cycle_patterns
        if self.gdb.run_to_label("cycle_patterns") == False:
            return 0
        # validate sensible values
        data_at_special_address = self.gdb.read_word(SPECIAL_ADDRESS)
        self.comment("Data at {sa:#x} should be {max_fib:#x}. Found to be {found:#x}".format( \
                    sa = SPECIAL_ADDRESS, max_fib = FIB_NUMBERS[-1], found = data_at_special_address))
        if  data_at_special_address != FIB_NUMBERS[-1]:
            self.comment("Incorrect. 0/2")
            return 0
        else:
            self.comment("Correct. 2/2")
            return 2

    def part3_tests(self):
        self.gdb.soft_reset()
        # run to initialisations_complete
        if self.gdb.run_to_label("initialisations_complete") == False:
            raise Exception("Label not hit second time? That can't be possible...")
        # set illegal value in start of RAM
        self.comment("Setting 0x20000000 to {sa:#x}".format(sa = ILLEGAL_ADDRESS))
        self.gdb.write_word(0x20000000, ILLEGAL_ADDRESS)
        # continue and verify that pattern is 0xAA
        if self.gdb.run_to_label("HardFault_Handler") == False:
            return 0
        self.gdb.send_continue()
        pattern_on_leds =  self.ii.read_port(0) 
        if pattern_on_leds != 0xAA:
            self.comment("HardFault handler expected to produce pattern 0xAA but instead got {p:#x}".format(\
                        p = pattern_on_leds))
            return 0
        self.comment("HardFault handler hit on illegal value and displaying 0xAA. 1/1")
        return 1
        
    def part4_tests(self):
        # reset
        self.gdb.send_control_c()
        self.gdb.soft_reset()
        if self.gdb.run_to_label("initialisations_complete") == False:
            raise Exception("Label not hit third time? That can't be possible...")
        # run to initialisations_complete 
        # set start of ram to some sensible value
        self.comment("Setting 0x20000000 to {sa:#x}".format(sa = SPECIAL_ADDRESS))
        self.gdb.write_word(0x20000000, SPECIAL_ADDRESS)
        # set breakpoint on  delay_routine
        if self.gdb.run_to_label("initialisations_complete") == False:
            return 0
        # run to breakpoint in a loop until pattern 0x81 is found.
        self.comment("Running to 'delay_routine' in a loop until pattern 0x81 found")
        pattern_found = False
        for i in range(0, 10):
            self.gdb.run_to_label("delay_routine")
            if self.ii.read_port(0) == 0x81:
                pattern_found = True
                break
        if pattern_found == False:
            self.comment("Could not find 0x81 on LEDs after 10 loop itterations. Aborting")
            return 0
        self.comment("Found 0x81. Now checking the rest of the patterns by running to 'delay_routine'.")
        # run to delay_routine again. Verify that next pattern until all patterns
        pattern_array = [0xC3, 0xE7, 0xFF, 0x7E, 0x3C, 0x18]
        for idx, val in enumerate(pattern_array):
            self.gdb.run_to_label("delay_routine")
            pattern_on_leds = self.ii.read_port(0)
            if pattern_on_leds != pattern_array[idx]:
                self.comment("On loop iteration number {lp} the pattern {found:#x} was found but should be {exp:#x}".format(
                            lp = idx, found = pattern_on_leds, exp = val))
            return 0
        # continue
        self.comment("All patterns found to use 'delay_routine'")
        self.comment("Now testing time between patterns")
        self.gdb.send_continue()
        # verify all patterns with 0.5 delay between.
        for i in range(0, len(pattern_array) - 1):
            delay = self.ii.pattern_timing(pattern_array[i], pattern_array[i+1])
            if delay > 0.52 or delay < 0.48:
                self.comment("Delay between {p1:#x} and {p2:#x} found to be {d}. 0/2".format(
                            p1 = pattern_array[i], p2 = pattern_array[i+1], d = delay))
                return 0
        self.comment("Delays found to be correct. 2/2")
        return 2

