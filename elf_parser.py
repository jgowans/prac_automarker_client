import subprocess

def get_address_of_label(elf, label):
    objdump = subprocess.Popen(["arm-none-eabi-objdump", "-t", elf], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if objdump.wait() != 0:
        raise Exception
    out = objdump.communicate()
    lines = out[0].splitlines()
    for l in lines:
        if label in l.decode():
            clean_l = l.decode().strip()
            split_l = clean_l.split()
            address_str = split_l[0]
            return int(address_str, 16)

    raise Exception("Label {} not found in .elf file".format(label))

