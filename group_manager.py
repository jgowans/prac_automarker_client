import csv
import logging
import time
import os
import subprocess

class Group:
    def __init__(self, members):
        self.members = members
        self.comment = "Undefined"
        self.directory = None
        self.mark = -1
        self.submissiontime = None
        self.src_file = None
    
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
        if len(all_files) == 1:
            self.src_file = all_files[0]
        else:
            assembly_files = [fi for fi in all_files if fi.endswith(".s")]
            if len(assembly_files) == 1:
                self.src_file = assembly_files[0]
        
        if self.src_file is None:
            logging.info("No file among {} matched for group: ".format(all_files, self.members))

    def build_submission(self):
        os.chdir(self.directory + "/Submission attachment(s)/")
        all_files = os.listdir()
        if len(all_files) is not 1:
            self.comment = "Multiple files found. I don't know which to mark."
            logging.info("Multiple files found for {}".format(self.members))
            mark = 0
            return
        if all_files[0].endswith(".s") != True:
            self.comment = "No file ending in .s found"
            logging.info("{} for group {}".format(self.comment, self.members))
            mark = 0
            return
        self.src_file = all_files[0]
        logging.debug("Attempting to build {} for group: {}".format(self.src_file, self.members))
        self.comment += "Attempting to compile file: \n".format(self.src_file)
        as_proc = subprocess.Popen(["arm-none-eabi-as", "-o", "main.o", self.src_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if (as_proc.wait() != 0):
            print(as_proc.communicate())
            mark = 0
            return

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




