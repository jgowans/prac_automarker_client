import serial
from interface_lib import InterrogatorInterface, GDBInterface, OpenOCD
import shlex, subprocess
import time


def run_tests(elf, comment):
    mark = 0
    comment("Starting to run prac 1 tests")
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
            # run to copy_to_RAM_complete
            if gdb.run_to_label("copy_to_RAM_complete") == False: # could not find label
                comment("Could not find label: copy_to_RAM_complete. Mark = 0")
                return mark
            comment("Now verifying the first four words in RAM")
            # verify the 4 words, awarding a mark for each
            mark += verify_word(gdb, comment, 0x20000000, 0xAABBCCDD)
            mark += verify_word(gdb, comment, 0x20000004, 0x00001122)
            mark += verify_word(gdb, comment, 0x20000008, 0x00002233)
            mark += verify_word(gdb, comment, 0x2000000c, 0x55555555)
            # modify the 4 words
            comment("Modifying 0x20000000 to be 0xFF")
            gdb.write_word(0x20000000, 0xFF)
            comment("Modifying 0x20000004 to be 0xAA")
            gdb.write_word(0x20000004, 0xAA)
            comment("Modifying 0x20000008 to be 0x42")
            gdb.write_word(0x20000008, 0x42)
            comment("Modifying 0x2000000c to be 0x69")
            gdb.write_word(0x2000000c, 0x69)
            # move data into 0x20000020
            gdb.write_word(0x20000020, 0x55)
            # run to infinite_loop
            if gdb.run_to_label("infinite_loop") == False:
                comment("Could not find label: infinite_loop. Aborting.")
                return mark
            # verify the 4 words
            mark += verify_word(gdb, comment, 0x20000010, 0x55)
            mark += verify_word(gdb, comment, 0x20000014, 0x1eb)
            mark += verify_word(gdb, comment, 0x20000018, 0xE8)
            mark += verify_word(gdb, comment, 0x2000001c, 0x2bd4)
            # query pattern on LEDs
    
    comment("All tests complete. Mark: {m}".format(m=mark))
    return mark


def verify_word(gdb, comment, address, data):
    if gdb.read_word(address) == data:
        comment("Word at {addr:#x} is correct. 1/1".format(addr = address))
        return 1
    else:
        comment("Word at {addr:#x} is incorrect: {val:#x}. 0/1".format(addr = address, val = gdb.read_word(address)))
        return 0


def scale_mark(mark, submission_time, comment):
    comment("Scaling PRAC1 mark by factor dependant on submission time")
    if submission_time < time.strptime("4 August 2014 10:00", "%d %B %Y %H:%M"):
        comment("3 marks awarded based on submission time")
        mark += 3
    elif submission_time < time.strptime("5 August 2014 10:00", "%d %B %Y %H:%M"):
        comment("2 marks awarded based on submission time")
        mark += 2
    elif submission_time < time.strptime("6 August 2014 10:00", "%d %B %Y %H:%M"):
        comment("1 marks awarded based on submission time")
        mark += 1
    else:
        comment("No marks awarded based on submission time")
        mark += 0
    return mark


