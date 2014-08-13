import serial
import interface_lib
import shlex, subprocess
import time


def run_prac1_tests(elf):
    comment = ""
    mark = ""
    comment += "Starting to run prac 1 tests\r\n"
    try:
        ii = InterrogatorInterface()
        comment += ii.comms_test()
        ii.reset(0) # pull line low. This does a reset
        openocdcmd = shlex.split("openocd -f interface/stlink-v2.cfg -f target/stm32f0x_stlink.cfg -c init -c \"reset halt\"")
        openocd = subprocess.Popen(openocdcmd, stderr=subprocess.DEVNULL)
        time.sleep(0.2)
        ii.reset(1) # release line. Allows code to run.
        with GDBInterface() as gdb:
            try:
                gdb.connect()
            except Exception as e:
            gdb.open_file(elf)
            gdb.erase()
            # load
            # run to copy_to_RAM_complete
            # verify the 4 words, awarding a mark for each
            # modify the 4 words
            # move data into 0x20000020
            # run to infinite_loop
            # verify the 4 words
            # query pattern on LEDs

    except Exception as e:
        comment += str(e)
        return [0, comment]  # got an exception - must return 0 mark

    finally:
        try:
            openocd.terminate()
        except: 
            pass

def verify_word(gdb, address, data):
    if gdb.read_word(address) == data:
        return [1, "Data: {} successfully found at address: {}. 1/1".format(data, address)]
    return [0, "Expected data: {} NOT found at address: {}. 0/1".format(data, address)]


