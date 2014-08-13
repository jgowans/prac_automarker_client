import csv
import logging
import time
import os
import subprocess
import elf_parser

class Group:
    def __init__(self, members):
        self.members = members
        self.comment_str = ""
        self.directory = None
        self.mark = -1
        self.submissiontime = None
        self.src_file = None

    def comment(self, to_append):
        self.comment_str += str(to_append)
        self.comment_str += "\n"
    
    def get_submissiontime(self):
        with open(str(self.directory) + "/timestamp.txt") as timefile:
            timestamp = timefile.readline() # will return something like: '20140805211624959'
            self.submissiontime = time.strptime(timestamp[0:14], "%Y%m%d%H%M%S") # prune off the miliseconds
            logging.debug("Submissiontime of {} assigned to {}".format(time.strftime("%a:%H:%M", self.submissiontime), str(self.members)))

    def find_src_file(self):
        '''The matchin process is to 
        - first check for a main.s file
        - if not found, check if only 1 file submitted
        - if multiple files submitted, check if only one ends in a .s extension'''
        os.chdir(self.directory + "/Submission attachment(s)/")
        all_files = os.listdir()
        assembly_files = [fi for fi in all_files if fi.endswith(".s")]
        if len(assembly_files) == 1:
            self.src_file = assembly_files[0]
            return True
        elif len(assembly_files) == 0:
            logging.info("No file among {} matched for group: ".format(all_files, self.members))
            self.comment("No suitable source file found")
            mark = 0
        else:
            self.comment("Multiple .s files found. I don't know which to mark.")
            logging.info("Multiple .s files found for {}".format(self.members))
        return False

    def build_submission(self):
        if self.find_src_file() == False:
            return
        logging.debug("Attempting to build {} for group: {}".format(self.src_file, self.members))
        self.comment("Attempting to compile file: {}".format(self.src_file))
        as_proc = subprocess.Popen(["arm-none-eabi-as", "-mcpu=cortex-m0", "-mthumb", "-g", "-o", "main.o", self.src_file], \
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if (as_proc.wait() != 0):
            error_message = as_proc.communicate()
            self.comment("Compile failed. Awarding 0. Error message:")
            self.comment(error_message[0])
            self.comment(error_message[1])
            logging.info("For group {} got error: \n {}".format(self.members, self.comment_str))
            mark = 0
            return
        self.comment("Compile succeeded. Attempting to link.")
        ld_proc = subprocess.Popen(["arm-none-eabi-ld", "-Ttext=0x08000000", "-o", "main.elf", "main.o"], \
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if (ld_proc.wait() != 0):
            error_message = ld_proc.communicate()
            self.comment("Link failed. Awarding 0. Error message:")
            self.comment(error_message[0])
            self.comment(error_message[1])
            logging.info("For group {} got error: \n {}".format(self.members, self.comment_str))
            mark = 0
            return
        self.comment("Link succeeded. Now running tests")
        elf_parser.get_address_of_label("main.elf", "copy_to_RAM_complete")


class GroupManager:
    def __init__(self, filename):
        logging.info("initialising a groups manager")
        self.groups = [] # a dict mapping a group number to a list of stdnums
        self.group_pointer = 0
        with open(filename) as groupsfile:
            groupsfile_reader = csv.reader(groupsfile, delimiter=',')
            for group in groupsfile_reader:
                # prune all empty members, then initialise the marks and comments dicts
                if group.count('') == 1:
                    group.remove('')
                self.groups.append(Group(group))
        logging.info("group creating completed with a total of {groupnums} groups.".format(groupnums=len(self.groups)))

    def has_next(self):
        if self.group_pointer < len(self.groups):
            return True
        return False

    def restart(self):
        self.group_pointer = 0

    def next(self):
        if self.group_pointer == len(self.groups):
            logging.error("tried to acces group after no more groups")
            raise Exception
        self.group_pointer += 1
        return self.groups[self.group_pointer - 1]

    def generate_output():
        pass




