import pexpect

class OpenOCD:
    def __init__(self, comment):
        self.comment = comment
        comment("Attempting to launch OpenOCD")
        openocdcmd = shlex.split("openocd -f interface/stlink-v2.cfg -f target/stm32f0x_stlink.cfg -c init -c \"reset halt\"")
        self.openocd = subprocess.Popen(openocdcmd, stderr=subprocess.DEVNULL)
        time.sleep(0.5)
        if self.openocd.poll() == None:
            comment("OpenOCD running")
        else:
            raise Exception("OpenOCD not running, but should be")

    def exit(self):
        self.openocd.kill()

    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        self.exit()

    def poll(self):
        return self.openocd.poll()
