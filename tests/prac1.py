import serial
import interface_lib
import shlex, subprocess
import time


def run_tests(elf, comment):
    mark = 0
    comment("Starting to run prac 1 tests")
    try:
        ii = InterrogatorInterface()
        comment(ii.comms_test())
        ii.reset(0) # pull line low. This does a reset
        with OpenOCD() as openocd:
            time.sleep(0.2)
            ii.reset(1) # release line. Allows code to run.
            with GDBInterface(elf) as gdb:
                gdb.connect()
                gdb.open_file()
                # gdb.erase()
                # load
                # run to copy_to_RAM_complete
                # verify the 4 words, awarding a mark for each
                # modify the 4 words
                # move data into 0x20000020
                # run to infinite_loop
                # verify the 4 words
                # query pattern on LEDs

        return mark

    except Exception as e:
        comment(str(e))
        return 0  # got an exception - must return 0 mark

def verify_word(gdb, address, data):
    if gdb.read_word(address) == data:
        return [1, "Data: {} successfully found at address: {}. 1/1".format(data, address)]
    return [0, "Expected data: {} NOT found at address: {}. 0/1".format(data, address)]

def scale_mark(mark, submission_time, comment):
    comment("Scaling PRAC1 mark by factor dependant on submission time")
    if submission_time < time.strptime("4 August 2014 10:00", "%d %B %Y %H:%M"):
        self.comment("3 marks awarded based on submission time")
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


