import os
import pexpect

def prac1_run(base_directory):
  mark = 0
  comment = ""
  elf = base_directory + "/Submission(s)/" + "main.elf"
  if os.path.isfile(elf) == False:
    return [mark, comment]
  gdb = pexpect.spawn("arm-none-eabi-gdb", timeout = 3)
  gdb.expect("(gdb)")
  erase_and_load(elf, gdb)

def erase_and_load(elf, gdb):
  gdb.sendline("tar rem :3333")
  gdb.expect("(gdb)")
  gdb.sendline("monitor flash_erase 0 0 0")
  gdb.expect("(gdb)")
  gdb.sendline("file " + str(elf))
