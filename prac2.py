import serial
from interface_lib import InterrogatorInterface, GDBInterface, OpenOCD
import shlex, subprocess
import time
import random


def run_tests(elf, comment):
    mark = 0
    comment("Starting to run prac 2 tests")
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

            if gdb.run_to_label("all_off") == False:
                comment("Could not hit label 'all off'. Aborting")
                return mark
            # ensure that only the correct pins are set as outputs:
            if gdb.read_word(0x48000400) <= 0x5555:
                comment("Only the lower byte of port B set to outputs. 1/1")
                mark += 1
            else:
                comment("More than the lower byte of port B set to outputs. 0/1") 

            for label, expected in [["display_AA", 0x00], ["all_on", 0xAA], ["bonus", 0xFF]]:
                if gdb.run_to_label(label) == False:
                    comment("Could not hit label '{l}'. Aborting".format(l=label))
                    return mark
                led_data = ii.read_port(0)
                if led_data == expected:
                    mark_to_add = 2
                else:
                    mark_to_add = 0
                comment("LED data should be {exp:#X} and is {led:#X}: {toadd}/2".format(exp = expected, led=led_data, toadd=mark_to_add))
                mark += mark_to_add

            comment("Attempting bonus")    
            gdb.delete_all_breakpoints()
            bonus_correct = True
            for i in range(0, 7): # checking the bonus 7 times.
                if [0, 1, 1, 1, 0, 0, 1][i] == 1: # sequence of button pushes and not pushes
                    ii.highz_pin(0) # simulate a button release
                    comment("Simulating not pushing SW0")
                    if gdb.run_to_label("all_off") == False:
                        comment("Could not hit label 'all_off' implying that you don't have a loop. Aborting")
                        return mark
                    if ii.read_port(0) != 0xFF: # should be all on when not pushing button
                        comment("Excpected 0xFF on the LEDs but got {led:#X}".format(led = ii.read_port(0)))
                        bonus_correct = False
                        break
                    comment("Expected 0xFF on LEDs and got it")
                else:
                    ii.clear_pin(0) # simulate a button push
                    comment("Simulating pushing SW0")
                    if gdb.run_to_label("all_off") == False:
                        comment("Could not hit label 'all_off' implying that you don't have a loop. Aborting")
                        return mark
                    if ii.read_port(0) != 0x55:
                        comment("Excpected 0x55 on the LEDs but got {led:#X}".format(led = ii.read_port(0)))
                        bonus_correct = False
                        break
                    comment("Expected 0x55 on LEDs and got it")


            if bonus_correct == True:
                comment("Bonus correct! :-). 2/0")
                mark += 2
            else:
                comment("Bonus not done. 0/0")

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
    comment("Scaling PRAC2 mark by factor dependant on submission time")
    if submission_time < time.strptime("11 August 2014 10:00", "%d %B %Y %H:%M"):
        comment("1.0 scale factors awarded based on submission time")
        mark = mark * 1.0
    elif submission_time < time.strptime("12 August 2014 10:00", "%d %B %Y %H:%M"):
        comment("0.9 scale factor awarded based on submission time")
        mark = mark * 0.9
    elif submission_time < time.strptime("13 August 2014 10:00", "%d %B %Y %H:%M"):
        comment("0.8 scale factor awarded based on submission time")
        mark = mark * 0.8
    else:
        comment("0.7 scale factor awarded based on submission time")
        mark = mark * 0.7
    return round(mark, 1)


