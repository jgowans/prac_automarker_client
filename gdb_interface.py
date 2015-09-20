import pexpect
import re
import elf_parser

class GDBException(Exception):
    pass
class BreakpointNotHit(GDBException):
    pass
class LabelNotFound(GDBException):
    pass

class GDBInterface:
    def __init__(self, logger):
        self.logger = logger
        self.gdb = pexpect.spawn("arm-none-eabi-gdb", timeout=10)
        self.gdb.expect_exact("(gdb)")
        # disables the "Type <return> to continue, or q <return> to quit"
        self.gdb.sendline("set pagination off")
        self.gdb.expect_exact("(gdb)")
        self.gdb.sendline("set logging file /tmp/automarker_gdb.log")
        self.gdb.expect_exact("(gdb)")
        self.gdb.sendline("set logging on")
        self.gdb.expect_exact("Copying output to")
        self.gdb.expect_exact("(gdb)")

    def terminate(self):
        self.gdb.terminate()

    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        self.terminate()

    def open_file(self, elf_file):
        self.elf_file = elf_file
        self.gdb.sendline("file \"{}\"".format(elf_file))
        # we'll either get a done or a no such file
        if self.gdb.expect(["done.*\(gdb\)", "No such file or directory"]) == 0:
            self.logger.debug( "file {} opened in GDB".format(elf_file))
        else:
            raise Exception("FATAL: Could not open file {} in GDB".format(elf_file))

    def connect(self):
        self.gdb.sendline("target remote localhost:3333")
        if self.gdb.expect([".*using localhost:3333[\s\S]*\([\s\S]*\)[\s\S]*\(gdb\)", \
                "Remote communication error",\
                "Connection timed out", "Remote connection closed"]) == 0:
            self.logger.debug("GDB connected to openOCD")
        else:
            raise Exception("FATAL: GDB could not connect to openOCD\r\n")

    def send_raw_command(self, cmd):
        self.gdb.sendline(cmd)
        self.gdb.expect_exact("(gdb)")
        return self.gdb.before.decode()

    def soft_reset(self):
        self.logger.debug("Attempting soft reset.")
        self.gdb.sendline("monitor reset halt")
        self.gdb.expect("target state: halted.*\(gdb\)")
        self.logger.debug("Soft reset complete.")

    def erase(self):
        self.gdb.sendline("monitor flash erase_sector 0 0 0")
        self.gdb.expect("erased sectors 0 through 0 on flash bank 0 in.*\(gdb\)")
        self.logger.debug("Microcontroller flash memory erased")

    def load(self):
        self.gdb.sendline("load")
        self.gdb.expect("Transfer rate.*\(gdb\)")
        self.logger.info(".elf file loaded into flash")

    def send_continue(self):
        self.logger.debug("Continuing code")
        self.gdb.sendline("continue")
        self.gdb.expect_exact("Continuing.")
        self.logger.info("Code now running.")

    def get_backtrace(self):
        self.gdb.sendline("backtrace")
        self.gdb.expect_exact("(gdb)")
        return self.gdb.before.strip()

    def send_control_c(self):
        self.logger.info("Sending Ctrl+C")
        self.gdb.sendcontrol('c')
        self.gdb.expect_exact("(gdb)")

    def run_to_address(self, address):
        self.logger.debug("break *{a:#X}".format(a = address))
        self.gdb.sendline("break *{a:#x}".format(a = address))
        try:
            self.gdb.expect_exact("(gdb)")
            self.gdb.sendline("continue")
            self.gdb.expect("Breakpoint([\s\S])*\(gdb\)")
            self.logger.debug("Hit breakpoint")
            self.delete_all_breakpoints()
        except Exception as e:
            print(e)
            self.logger.critical("Breakpoint not hit. Code may have hard-faulted, or stuck in a loop?")
            self.send_control_c()
            self.delete_all_breakpoints()
            self.logger.critical("Backtrace:\n" + self.get_backtrace().decode())
            raise BreakpointNotHit

    def run_to_label(self, label):
        try:
            address = elf_parser.get_address_of_label(self.elf_file, label) # this will throw an exception if label not found
            self.logger.info("Attempting to run to label {l} with address {a:#X}".format(l = label, a = address))
        except:
            self.logger.critical("Could not find label: {l}".format(l = label))
            raise LabelNotFound
        self.run_to_address(address)

    def run_to_function(self, f_name):
        self.logger.info("Attempting to run to label {l}".format(l = f_name))
        self.logger.debug("break {l}".format(l = f_name))
        self.gdb.sendline("break {l}".format(l = f_name))
        try:
            self.gdb.expect_exact("(gdb)")
            self.gdb.sendline("continue")
            self.gdb.expect("Breakpoint.*\(gdb\)")
            self.logger.info("Hit breakpoint")
            self.delete_all_breakpoints()
            return True
        except:
            self.logger.critical("Breakpoint never hit. Code may have hard-faulted, or stuck in a loop?")
            self.send_control_c()
            return False

    def read_word(self, address):
        self.gdb.sendline("x/1wx {a:#x}".format(a = address))
        self.gdb.expect("{0:#x}\s?\S*:".format(address))
        self.gdb.expect_exact("(gdb)")
        return int(self.gdb.before.strip(), 16)

    def write_word(self, address, data):
        set_string = "set {{int}}{a:#x} = {d:#x}".format(a = address, d = data)
        self.gdb.sendline(set_string)
        self.gdb.expect_exact("{}\r\n(gdb)".format(set_string))
    
    def delete_all_breakpoints(self):
        self.gdb.sendline("delete")
        self.gdb.expect_exact("Delete all breakpoints? (y or n) ")
        self.gdb.sendline("y")
        self.gdb.expect_exact("(gdb)")
        self.logger.debug("All previous breakpoints deleted")

    def get_function_prototype(self, f_name):
        self.gdb.sendline("info functions ^{f}$".format(f=f_name))
        self.gdb.expect_exact("All functions matching regular expression")
        self.gdb.expect_exact("(gdb)")
        raw_functions = self.gdb.before.strip().decode()
        raw_functions_lines = raw_functions.split('\n')
        functions = []
        function_re = re.compile(".*\(.*\);")
        for l in raw_functions_lines:
            if function_re.match(l):
                functions.append(l)
        return functions

    def get_all_global_variables(self):
        self.gdb.sendline("info variables")
        self.gdb.expect("(gdb)")
        all_vars = self.gdb.before.decode().split("\n")
        all_vars = [v.strip() for v in all_vars]
        all_defined_idx = all_vars.index("All defined variables:")
        non_debugging_idx = all_vars.index("Non-debugging symbols:")
        global_vars = []
        for idx in range(all_defined_idx + 1, non_debugging_idx):
            if all_vars[idx] != '':
                global_vars.append(all_vars[idx])
        return global_vars

    def get_variable_type(self, var):
        var_string = "whatis {v}".format(v = var)
        self.gdb.sendline(var_string)
        self.gdb.expect("type = .*") # expecting something like: $6 = 0x7b
        value = self.gdb.after.decode().split('=')[1].strip() # should get the '0x7b' of the above
        self.gdb.expect_exact("(gdb)")
        return value

    def get_variable_value(self, var):
        var_string = "print/x {v}".format(v = var)
        self.gdb.sendline(var_string)
        if self.gdb.expect(["\$.* = .*\n", "No symbol .* in current context"]) != 0: # expecting something like: $6 = 0x7b
            raise Exception("Symbol not found")
        value = self.gdb.after.decode().split('=')[1].strip() # should get the '0x7b' of the above
        self.gdb.expect_exact("(gdb)")
        return int(value, 16)

    def set_variable_value(self, var, value):
        set_string = "set {v}={val}".format(v = var, val=value)
        self.gdb.sendline(set_string)
        self.gdb.expect_exact("(gdb)")

    def send_finish(self):
        self.gdb.sendline("finish")
        self.gdb.expect_exact("Run till exit from")
        self.gdb.expect_exact("(gdb)")
