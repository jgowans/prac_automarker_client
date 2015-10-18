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
class SourceFileProblem(PracFailedError):
    pass

class PracTests:
    def __init__(self, submitter, logger):
        self.logger = logger
        self.submitter = submitter

    def run_tests(self):
        self.ii = InterrogatorInterface()
        self.ii.reset(0) # pull NRST low
        time.sleep(1)
        with OpenOCD(self.logger.getChild('openocd')) as openocd:
            self.ii.reset(1) # release NRST to allow openocd to connect
            time.sleep(0.5)
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

    def unzip_submission(self):
        os.chdir(self.submitter.submission_directory)
        all_files = os.listdir()
        self.logger.info("Before unzip, directory contains: {f}".format(f = all_files))
        zip_files = [fi for fi in all_files if fi.endswith(".zip")]
        if len(zip_files) != 1:
            self.logger.critical("Too many or not enough zip files found out of: {a}. Aborting.".format(a = all_files))
            raise SourceFileProblem
        self.logger.info("Extracting zipfile: {z}".format(z = zip_files[0]))
        try:
            with zipfile.ZipFile(zip_files[0]) as z:
                    z.extractall()
        except zipfile.BadZipFile as e:
            self.logger.critical(str(e))
            raise BuildFailedError
        all_files = os.listdir()
        self.logger.info("After unzip, directory contains: {f}".format(f = all_files))

    def build(self):
        raise NotImplementedError
    
    def run_specific_prac_tests(self):
        raise NotImplementedError

    def catalogue_submission_files(self):
        raise NotImplementedError

