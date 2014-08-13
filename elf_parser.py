import subprocess

def get_address_of_label(elf, label):
    objdump = subprocess.Popen(["arm-none-eabi-objdump", "-t", elf], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if objdump.wait() != 0:
        raise Exception
    out = objdump.communicate()
    lines = out[0].splitlines()
    for l in lines:
        if label in str(l):
            clean_l = str(l).strip()
            split_l = clean_l.split()
            return "0x{}".format(split_l[0])

    raise Exception

