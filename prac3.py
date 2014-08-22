import serial
from interface_lib import InterrogatorInterface, GDBInterface, OpenOCD
import shlex, subprocess
import time
import random


def run_tests(elf, comment):
    mark = 0
    comment("Starting to run prac 3 tests")
    ii = InterrogatorInterface()
    comment(ii.comms_test())
    ii.reset(0) # pull line low. This does a reset
    with OpenOCD(comment) as openocd:
        time.sleep(0.2)
        ii.reset(1) # release line. Allows code to run.
        with GDBInterface(elf, comment) as gdb:
            gdb.open_file()
            gdb.connect()
            gdb.erase()
            gdb.load()
            gdb.send_continue()
            # assert no button, ensure that AA->55->AA timing is 0.47-0.53 2/2
            comment("=== Part 1 ===")
            mark += part1_tests(ii, comment)

            comment("===Part 2 ===")
            mark += part2_tests(ii, comment)
            
            comment("=== Part 3 ===")
            mark += part3_tests(ii, comment)

            ii.highz_pin(0)
            ii.highz_pin(1)
    
    comment("All tests complete. Mark: {m}".format(m=mark))
    return mark

def scale_mark(mark, submission_time, comment):
    comment("Scaling PRAC3 mark by factor dependant on submission time")
    comment("No scale factor implemented for this prac.")
    return mark

def part1_tests(ii, comment):
    ii.highz_pin(0)
    ii.highz_pin(1)
    time.sleep(0.5)
    comment("Not pressing either SW0 or SW1")
    for pattern0, pattern1  in [[0x55, 0xAA], [0xAA, 0x55]]:
        comment("Checking timing for pattern transition: {p0:#X}->{p1:#X}->{p0:#X}".format(p0 = pattern0, p1 = pattern1))
        timing = round(ii.pattern_timing(pattern0, pattern1), 2)
        if timing == -1:
            comment("Could not find patterns within a timeout of 3 seconds. Aborting.")
            return 0
        comment("Timing should be between 0.47 and 0.53 seconds. Found to be {t} seconds.".format(t=timing))
        if timing >= 0.47 and timing <= 0.53:
            comment("Correct.")
        elif timing >= 0.42 and timing <= 0.58:
            comment("Outside of bounds. 2/4")
            return 2
        else:
            comment("Far outside of bounds. 0/4")
            return 0
    comment("Both tests correct. 4/4")
    return 4

def part2_tests(ii, comment):
    ii.clear_pin(0) # simulate a button push
    ii.highz_pin(1)
    time.sleep(0.5)
    # Ensure that timimg 0x00-FF-00 is 0.47-0.53: 
    # Ensure that timimg 00-FF-00 is 0.47-0.53
    for pattern0, pattern1,  in [[0xFF, 0x00], [0x00, 0xFF]]:
        comment("Checking timing for pattern transition: {p0:#X}->{p1:#X}->{p0:#X}".format(p0 = pattern0, p1 = pattern1))
        timing = round(ii.pattern_timing(pattern0, pattern1), 2)
        if timing == -1:
            comment("Could not find patterns within a timeout of 3 seconds. Aborting.")
            return 0
        comment("Timing should be between 0.47 and 0.53 seconds. Found to be {t} seconds.".format(t=timing))
        if timing >= 0.47 and timing <= 0.53:
            comment("Correct.")
        elif timing >= 0.42 and timing <= 0.58:
            comment("Outside of bounds. 1/3")
            return 1
        else:
            comment("Far outside of bounds. 0/3")
            return 0
    comment("Both tests correct. 3/3")
    return 3

def part3_tests(ii, comment):
    # simulate SW1 and not SW0. Should be flashing AA,55 at 0.25 seconds
    ii.highz_pin(0)
    ii.clear_pin(1)
    time.sleep(0.5)
    comment("Pressing SW1 and releasing SW0")
    for pattern0, pattern1  in [[0x55, 0xAA], [0xAA, 0x55]]:
        comment("Checking timing for pattern transition: {p0:#X}->{p1:#X}->{p0:#X}".format(p0 = pattern0, p1 = pattern1))
        timing = round(ii.pattern_timing(pattern0, pattern1), 2)
        if timing == -1:
            comment("Could not find patterns within a timeout of 3 seconds. Aborting.")
            return 0
        comment("Timing should be between 0.23 and 0.27 seconds. Found to be {t} seconds.".format(t=timing))
        if timing < 0.23 or timing > 0.27:
            comment("Timing not correct. Aborting")
            return 0
        else: 
            comment("Correct.")
    ii.clear_pin(0)
    ii.clear_pin(1)
    time.sleep(0.5)
    comment("Pressing SW1 and pressing SW0")
    for pattern0, pattern1  in [[0xFF, 0x00], [0x00, 0xFF]]:
        comment("Checking timing for pattern transition: {p0:#X}->{p1:#X}->{p0:#X}".format(p0 = pattern0, p1 = pattern1))
        timing = round(ii.pattern_timing(pattern0, pattern1), 2)
        if timing == -1:
            comment("Could not find patterns within a timeout of 3 seconds. Aborting.")
            return 0
        comment("Timing should be between 0.23 and 0.27 seconds. Found to be {t} seconds.".format(t=timing))
        if timing < 0.23 or timing > 0.27:
            comment("Timing not correct. Aborting")
            return 0
        else: 
            comment("Correct.")
    comment("Part 3 correct. 2/2")
    return 2

