import time
from openocd import OpenOCD
from gdb_interface import GDBInterface
from interrogator_interface import InterrogatorInterface

class TestFailedError(Exception):
    pass

class PracTests:
    def __init__(self, group, logger):
        self.logger = logger
        self.group = group

    def run_tests(self):
        self.ii = InterrogatorInterface()
        self.ii.reset(0) # pull NRST low
        with OpenOCD(self.logger.getChild('openocd')) as openocd:
            time.sleep(0.2)
            self.ii.reset(1) # release NRST to allow openocd to connect
            with GDBInterface(self.logger.getChild('gdb')) as self.gdb:
                gdb.connect()
                # must be implemented in subclass
                self.run_specific_prac_tests()

    def build(self):
        raise NotImplementedError
    
    def run_specific_prac_tests(self):
        raise NotImplementedError

