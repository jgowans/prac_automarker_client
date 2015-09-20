import time
from openocd import OpenOCD
from gdb_interface import GDBInterface
from interrogator_interface import InterrogatorInterface
import subprocess
import shlex
import os

class PracFailedError(Exception):
    pass
class TestFailedError(PracFailedError):
    pass
class BuildFailedError(PracFailedError):
    pass

class PracTests:
    def __init__(self, student, logger):
        self.logger = logger
        self.student = student

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
        proc = subprocess.Popen(clean_full_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        try:
            return_code = proc.wait(10)
        except subprocess.TimeoutExpired:
            self.logger.critical("Process timed out. Killing it")
            os.system("sudo -u marker killall -s SIGKILL -u marker")
            raise BuildFailedError
        if return_code != 0:
            self.logger.critical("Non-zero return code received")
            error_message = proc.communicate()
            self.logger.critical(error_message[0].decode())
            self.logger.critical(error_message[1].decode())
            raise BuildFailedError

    def clean_marker_directory(self):
        self.exec_as_marker("rm -rf /home/marker/*")

    def build(self):
        raise NotImplementedError
    
    def run_specific_prac_tests(self):
        raise NotImplementedError

