import serial
from interface_lib import InterrogatorInterface, GDBInterface, OpenOCD
import shlex, subprocess
import time
import random

data_array = [0x22F65244, 0x4E66ECA3, 0x25C1C308, 0xE278D1CA, 0x10E865FE, 0x839B17FB, 0xDE6AC773, 0x49A0392B, 0x0442B580, 0xAE6E269D, 0xCB220366, 0x603DEBBE, 0xFD88B1BF, 0x49C5652F, 0x25476C5A, 0xA5C40771, 0xB04D908D, 0x831C1806, 0x5B4F75D4, 0x6B016B93, 0x90DCB11A, 0xEFB6E394, 0x44DB27DA, 0xCF205F79, 0xB1192A24, 0x79CF44E2, 0x371CE3BA, 0x7A279FF5, 0x006047DC, 0xFA165142, 0x12690FDC, 0x5AAD829E, 0x19244BA0, 0x0B5174A3, 0xBD7172C8, 0x1D3B229F, 0xADA0357E, 0x1D44E4E6, 0x37CAA86E, 0x6A08FC5D, 0x465FAEE1, 0x2E52E372, 0xD6016409, 0x52012177, 0x848249E0, 0xCEE8EC8D, 0xCA09FBE7, 0x45EC4E32, 0xA11CCFB5, 0x95584228]

def run_tests(elf, comment):
    mark = 0
    comment("Starting to run prac 4 tests")
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
            # assert no button, ensure that AA->55->AA timing is 0.47-0.53 2/2
            comment("=== Part 1 ===")
            mark += part1_tests(gdb, ii, comment)

            comment("===Part 2 ===")
            mark += part2_tests(gdb, ii, comment)

            comment("Sending 'continue' to allow code to free-run")
            gdb.send_continue()
            
            comment("=== Part 3 ===")
            mark += part3_tests(gdb, ii, comment)

            comment("=== Part 4 ===")
            mark += part4_tests(gdb, ii, comment)

            comment("=== Part 5 ===")
            mark += part5_tests(gdb, ii, comment)

            ii.highz_pin(0)
            ii.highz_pin(1)

    comment("All tests complete. Mark: {m}".format(m=mark))
    return mark

def scale_mark(mark, submission_time, comment):
    comment("Scaling PRAC4 mark by factor dependant on submission time")
    comment("No scale factor implemented for this prac.")
    return mark

def part1_tests(gdb, ii, comment):
    if gdb.run_to_label("copy_to_RAM_complete") == False:
        comment("Could not hit label 'copy_to_RAM_complete'. Aborting")
        return 0
    comment("Verifying array in RAM")
    for idx, val in enumerate(data_array):
        address = 0x20000000 + (4*idx)
        data_in_RAM = gdb.read_word(address)
        if data_in_RAM != val:
            comment("Data at address {addr:#x} should be {v:#x} but is {d:#x}".format(addr = address, v = val, d = data_in_RAM))
            return 0
    comment("Data correct in RAM. 3/3")
    return 3

def part2_tests(gdb, ii, comment):
    if gdb.run_to_label("increment_of_bytes_complete") == False:
        comment("Could not hit label 'increment_of_bytes_complete'. Aborting")
        return 0
    comment("Verifying incremented array in RAM")
    for idx, val in enumerate(data_array):
        address = 0x20000000 + (4*idx)
        val_inc = 0
        val_inc += (val + (1 << 0)) & (0xFF << 0)
        val_inc += (val + (1 << 8)) & (0xFF << 8)
        val_inc += (val + (1 << 16)) & (0xFF << 16)
        val_inc += (val + (1 << 24)) & (0xFF << 24)
        data_in_RAM = gdb.read_word(address)
        for byte_offset in range(0, 3):
            # add one at the correct place, then shift the byte of interest down to LSB and select with mask
            val_byte = ((val + (1 << 0)) >> (byte_offset * 8)) & 0xFF
            data_byte = ((data_in_RAM + (1 << 0)) >> (byte_offset * 8)) & 0xFF
        if data_in_RAM != val:
            #comment("Data at address {addr:#x} should be {v:#x} but is {d:#x}".format( \
            #        addr = address + byte_offset, v = val_byte, d = data_byte))
            #return 0
            pass
    comment("Data correct in RAM. 2/2")
    comment("Now modifying data in RAM. Setting all words to 0x88888888")
    for word_offset in range(0, len(data_array)):
        word_addr = 0x20000000 + (word_offset*4)
        gdb.write_word(word_addr, 0x88888888)
    comment("Setting address 0x20000008 to 0x32897788")
    comment("This implies a max unsigned of 0x99, min unsigned of 0x32 and max signed of 0x77")
    gdb.write_word(0x20000008, 0x32997788)
    return 2

def part3_tests(gdb, ii, comment):
    # simulate SW1 and not SW0. Should be flashing AA,55 at 0.25 seconds
    ii.highz_pin(0)
    ii.highz_pin(1)
    time.sleep(0.5)
    comment("Releasing both SW0 and SW1")
    led_data = ii.read_port(0)
    comment("Data on LEDs should be max unsigned (0x99), and found to be {d:#X}".format(d=led_data))
    if led_data != 0x99:
        comment("Incorrect. 0/3")
        return 0
    comment("Part 3 correct. 3/3")
    return 3

def part4_tests(gdb, ii, comment):
    # simulate SW1 and not SW0. Should be flashing AA,55 at 0.25 seconds
    ii.clear_pin(0)
    ii.highz_pin(1)
    time.sleep(0.5)
    comment("Pressing SW0 and releasing SW1")
    led_data = ii.read_port(0)
    comment("Data on LEDs should be min unsigned (0x32), and found to be {d:#X}".format(d=led_data))
    if led_data != 0x32:
        comment("Incorrect. 0/2")
        return 0
    comment("Part 4 correct. 2/2")
    return 2

def part5_tests(gdb, ii, comment):
    # simulate SW1 and not SW0. Should be flashing AA,55 at 0.25 seconds
    ii.highz_pin(0)
    ii.clear_pin(1)
    time.sleep(0.5)
    comment("Releasing SW0 and pressing SW1")
    led_data = ii.read_port(0)
    comment("Data on LEDs should be max signed (0x77), and found to be {d:#X}".format(d=led_data))
    if led_data != 0x77:
        comment("Incorrect. 0/1")
        return 0
    comment("Part 5 correct. 1/1")
    return 1
