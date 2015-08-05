import subprocess

def get_address_of_label(elf, label):
    objdump = subprocess.Popen(["arm-none-eabi-objdump", "-t", elf], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if objdump.wait() != 0:
        raise Exception
    out = objdump.communicate()
    lines = out[0].splitlines()
    for line in lines:
        line = l.decode().strip().split()
        if (len(l) == 5) and (l[4] == label):
            address_str = line[0]
            return int(address_str, 16)
    raise Exception("Label {} not found in .elf file".format(label))

def get_text_size(elf):
    objdump = subprocess.Popen(["size", elf], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if objdump.wait() != 0:
        raise Exception
    out = objdump.communicate()
    # will be something like:
    #   text    data     bss     dec     hex filename
    #    36        0       0      36      24 main.elf
    lines = out[0].splitlines()
    sizes_line = lines[1].split()
    text_size = sizes_line[0]
    return int(text_size)

