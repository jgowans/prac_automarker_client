import time
from openocd import OpenOCD
from gdb_interface import GDBInterface
from interrogator_interface import InterrogatorInterface
import subprocess
import shlex

class PracFailedError(Exception):
    pass
class TestFailedError(PracFailedError):
    pass
class BuildFailedError(PracFailedError):
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
                # must be implemented in subclass
                self.run_specific_prac_tests()

    def exec_as_marker(self, cmd):
        full_cmd = "sudo -u marker HOME=/home/marker sh -c 'cd /home/marker/; " + cmd + "'"
        self.logger.debug("Exec as marker: {c}".format(c = full_cmd))
        clean_full_cmd = shlex.split(full_cmd)
        subprocess.check_output(clean_full_cmd, stderr=subprocess.STDOUT, timeout=5)

    def clean_marker_directory(self):
        self.exec_as_marker("rm -rf /home/marker/*")

    def build(self):
        raise NotImplementedError
    
    def run_specific_prac_tests(self):
        raise NotImplementedError

