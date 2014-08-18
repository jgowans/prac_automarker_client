import csv
import logging
logger = logging.getLogger(__name__)
import time
import os
import subprocess
import prac2

class Group:
    def __init__(self, members):
        self.members = members
        self.comment_arr = []
        self.directory = None
        self.mark = 0
        self.submissioni_time = None
        self.src_file = None
        self.full_path_to_elf = None

    def comment(self, to_append):
        logger.info(to_append)
        self.comment_arr.append(str(to_append))
    
    def get_submissiontime(self):
        with open(str(self.directory) + "/timestamp.txt") as timefile:
            timestamp = timefile.readline() # will return something like: '20140805211624959'
            self.submission_time = time.strptime(timestamp[0:14], "%Y%m%d%H%M%S") # prune off the miliseconds
            self.comment("Submissiontime of {} assigned".format(time.strftime("%a:%H:%M", self.submission_time)))

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
            self.comment("Only 1 .s file submitted, namely: {}".format(self.src_file))
        elif "main.s" in assembly_files:
            self.src_file = "main.s"
            self.comment("Multiple .s files submitted: using main.s")
        else:
            self.comment("No suitable source file found out of: {fi}".format(fi = all_files))
            self.mark = 0

    def build_submission(self):
        if self.src_file == None:
            self.comment("Can't build - no source file")
            return
        self.comment("Checking start of file for student numbers")
        with open(self.src_file) as fi:
            l0 = fi.readline()
            stdnums_from_file = l0.split()
            stdnums_from_file = [s.strip('@ /') for s in stdnums_from_file] # remove any comment symbols or white space
            for grouped_student in self.members:
                if grouped_student not in stdnums_from_file:
                    self.comment("Student number: {} not found in starting line of source file".format(grouped_student))
                    self.comment("In future, the compile will abort here. Bypassing error this time.")
                    # return
        self.comment("Student numbers appeared correctly at start of file")
        self.comment("Attempting to compile file: {}".format(self.src_file))
        as_proc = subprocess.Popen(["arm-none-eabi-as", "-mcpu=cortex-m0", "-mthumb", "-g", "-o", "main.o", self.src_file], \
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if (as_proc.wait() != 0):
            error_message = as_proc.communicate()
            self.comment("Compile failed. Awarding 0. Error message:")
            self.comment(error_message[0])
            self.comment(error_message[1])
            self.mark = 0
            return
        self.comment("Compile succeeded. Attempting to link.")
        ld_proc = subprocess.Popen(["arm-none-eabi-ld", "-Ttext=0x08000000", "-o", "main.elf", "main.o"], \
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if (ld_proc.wait() != 0):
            error_message = ld_proc.communicate()
            self.comment("Link failed. Awarding 0. Error message:")
            self.comment(error_message[0])
            self.comment(error_message[1])
            self.mark = 0
            return
        self.full_path_to_elf = self.directory + "/Submission attachment(s)/main.elf"
        self.comment("Link succeeded")

    def run_tests(self):
        if self.full_path_to_elf == None:
            self.comment("Can't run tests as no elf exists")
            self.mark = 0
        else:
            self.comment("Starting to run tests")
            # would probably be better to do this with inheretance... 
            self.mark = prac2.run_tests(self.full_path_to_elf, self.comment)
            self.comment("Returned from running tests")

    def scale_by_factor(self):
        self.comment("Mark before scaling: {}".format(self.mark))
        self.mark = prac2.scale_mark(self.mark, self.submission_time, self.comment)
        self.comment("Mark after scaling: {}".format(self.mark))

    def write_comments_file(self):
        with open(self.directory + "/comments.txt", "w") as f:
            for c in self.comment_arr:
                f.write(c + "<br>\n")

    def clean(self):
        self.comment_arr = None # just free some memory

class GroupManager:
    def __init__(self, filename):
        logger.info("initialising a groups manager")
        self.groups = [] # a dict mapping a group number to a list of stdnums
        self.group_pointer = 0
        with open(filename) as groupsfile:
            groupsfile_reader = csv.reader(groupsfile, delimiter=',')
            for group in groupsfile_reader:
                # prune all empty members, then initialise the marks and comments dicts
                if group.count('') == 1:
                    group.remove('')
                self.groups.append(Group(group))
        logger.info("group creating completed with a total of {groupnums} groups.".format(groupnums=len(self.groups)))

    def has_next(self):
        if self.group_pointer < len(self.groups):
            return True
        return False

    def restart(self):
        self.group_pointer = 0

    def next(self):
        if self.group_pointer == len(self.groups):
            logger.error("tried to acces group after no more groups")
            raise Exception
        self.group_pointer += 1
        return self.groups[self.group_pointer - 1]

    def generate_marks_file(self, csvfilenew):
        rows =[]
        rows.append(["Practical2", "Points"])
        rows.append([])
        rows.append(["Display ID","ID","Last Name","First Name","grade"])

        for group in self.groups:
            for member in group.members:
                rows.append([member.lower(), member.lower(), "", "", str(group.mark),])
        with open(csvfilenew, 'w') as fi:
            new_writer = csv.writer(fi)
            for row in rows:
                new_writer.writerow(row)


