import csv
import logging
logger = logging.getLogger(__name__)
import time
import os
import subprocess
import elf_parser
import zipfile
import prac_exam_thu
import shutil


class Group:
    def __init__(self, members):
        self.members = members
        self.comment_arr = []
        self.directory = None
        self.mark = 0
        self.submissioni_time = None
        self.src_file = None
        self.test_runner = None

    def comment(self, to_append):
        logger.info(to_append)
        self.comment_arr.append(str(to_append))
    
    def get_submissiontime(self):
        if os.path.exists((str(self.directory) + "/timestamp.txt")):
            with open(str(self.directory) + "/timestamp.txt") as timefile:
                timestamp = timefile.readline() # will return something like: '20140805211624959'
                self.submission_time = time.strptime(timestamp[0:14], "%Y%m%d%H%M%S") # prune off the miliseconds
                self.comment("Submissiontime of {} assigned".format(time.strftime("%a:%H:%M", self.submission_time)))

    def unzip_submission(self):
        os.chdir(self.directory + "/Submission attachment(s)/")
        all_files = os.listdir()
        elf_files = [fi for fi in all_files if fi.endswith(".elf")]
        if len(elf_files) > 0:
            self.comment("Elf files exist before unzipping run: {e}".format(e = elf_files))
            for e in elf_files:
                os.remove(e)
            self.comment("Elf files deleted")
        zip_files = [fi for fi in all_files if fi.endswith(".zip")]
        if len(zip_files) != 1:
            self.comment("Too many or not enough zip file found out of: {a}".format(a = all_files))
            exit()
            self.comment("Aborting.")
            return False
        self.comment("Extracting zipfile: {z}".format(z = zip_files[0]))
        with zipfile.ZipFile(zip_files[0]) as z:
            z.extractall()
        all_files = os.listdir()
        self.comment("After extract, directory contains: {a}".format(a = all_files))
        elf_files = [fi for fi in all_files if fi.endswith(".elf")]
        if len(elf_files) > 0:
            self.comment("Elf files exist before unzipping run: {e}".format(e = elf_files))
            for e in elf_files:
                os.remove(e)
            self.comment("Elf files deleted")

    def find_src_file(self):
        '''The matchin process is to 
        - first check for a main.s file
        - if not found, check if only 1 file submitted
        - if multiple files submitted, check if only one ends in a .s extension'''
        os.chdir(self.directory + "/Submission attachment(s)/")
        all_files = os.listdir()
        c_files = [fi for fi in all_files if fi.endswith(".c")]
        if len(c_files) == 1:
            self.src_file = c_files[0]
            self.comment("Only 1 .c file submitted, namely: {}".format(self.src_file))
            return True
        elif "main.c" in c_files:
            self.src_file = "main.c"
            self.comment("Multiple .c files submitted: using main.c")
            return True
        else:
            print("No C files found for:")
            print(self.directory + "/Submission attachment(s)/")
            self.comment("No suitable source file found out of: {fi}".format(fi = all_files))
            return False

    def copy_src_to_centeral(self):
        os.chdir(self.directory + "/Submission attachment(s)/")
        new_name = str(self.members[0]) + "_" + self.src_file
        shutil.copyfile(self.src_file, "/tmp/plag_check/thu_prac_exam/" + new_name)

    def prepend_stdnums(self):
        if self.src_file is None:
            return False
        stdnum_str = "// {m}\n".format(m = str(self.members))
        with open(self.directory + "/Submission attachment(s)/" + self.src_file, "r") as f:
            src_code = f.read()
        with open(self.directory + "/Submission attachment(s)/" + self.src_file, "w") as f:
            f.write(stdnum_str + src_code)

    def build_submission(self):
        if self.src_file == None:
            self.comment("Can't build - no source file")
            return False
        self.comment("Checking start of file for student numbers")
        with open(self.src_file) as fi:
            line0 = fi.readline()
            for stdnum in self.members:
                if stdnum.upper() not in line0.upper():
                    self.comment("Student number: {s} not found in starting line of source file".format(s = stdnum))
                    return False
        self.comment("Student numbers appeared correctly at start of file")
        self.comment("Attempting to compile file: {}".format(self.src_file))
        self.test_runner = prac_exam_thu.PracExamThuTests(self.comment, self.directory + "/Submission attachment(s)/", self.src_file)
        if self.test_runner.build() == False:
            self.test_runner = None

    def run_tests(self):
        if self.test_runner == None:
            self.comment("Can't run tests as no elf exists")
            self.mark = 0
        else:
            self.comment("Starting to run tests")
            # would probably be better to do this with inheretance... 
            self.mark = self.test_runner.run_tests()
            self.comment("Returned from running tests")

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
        self.grades_filename = filename
        with open(filename) as groupsfile:
            groupsfile_reader = csv.reader(groupsfile, delimiter=',')
            for group in groupsfile_reader:
                # prune all empty members, then initialise the marks and comments dicts
                if len(group) == 6:
                    self.groups.append(Group([group[1]]))
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

    def generate_marks_file(self):
        rows =[]
        with open(self.grades_filename) as fi:
            old_reader = csv.reader(fi)
            for row in old_reader:
                rows.append(row)

        for group in self.groups:
            group_row = None # this will be a reference to the group's row
            if group.directory is not None: # ensure they submitted with a valid directory
                for member in group.members:
                    for row_to_check in rows:
                        if (len(row_to_check) == 6) and (member in row_to_check[1]): # std num found in Group column
                            if group_row == None: # not yet assigned - assign directly
                                group_row = row_to_check
                            else: # already assigned - ensure new assignment matches old
                                if row_to_check is not group_row:
                                    raise Exception("Group {g} found in two rows. 1: {r1}. 2: {r2}".format(g=group.members, \
                                            r1 = group_row, r2 = row_to_check))
                if group_row == None:
                    raise Exception("Group {g} submitted but no matching row found".format(g = group.members))
                group_row[4] = group.mark # group_row should be a reference to a row in rows, so this should update rows.
        # write back        
        with open(self.grades_filename + "_new", 'w') as fi:
            new_writer = csv.writer(fi)
            for row in rows:
                new_writer.writerow(row)


