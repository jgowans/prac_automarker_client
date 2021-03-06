import shlex
import subprocess
import time

class OpenOCD:
    def __init__(self, logger):
        self.logger = logger
        self.logger.debug("Attempting to launch OpenOCD")
        openocdcmd = shlex.split("openocd -f interface/stlink-v2.cfg -f target/stm32f0x_stlink.cfg -c init -c \"reset halt\"")
        self.logfile = open('/tmp/automarker_openocd.log', 'a')
        self.openocd = subprocess.Popen(openocdcmd, stderr=self.logfile, stdout=self.logfile)
        time.sleep(0.5)
        if self.openocd.poll() == None:
            self.logger.info("OpenOCD running")
        else:
            raise Exception("OpenOCD not running, but should be")

    def exit(self):
        self.openocd.kill()
        self.logfile.close()

    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        self.exit()

    def poll(self):
        return self.openocd.poll()
