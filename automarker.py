#!/usr/bin/env python3

BASE_DIR = "/tmp/Prac_Exam_Thursday/"

import os
import logging
import time
logging.basicConfig(filename = "/tmp/prac_exam_thursday_{t}.log".format(t = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())), \
        level=logging.INFO, format="%(asctime)s:" + logging.BASIC_FORMAT)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
logging.getLogger('').addHandler(console)
logger = logging.getLogger(__name__)
import csv
import group_manager

logger.info("Automarker beginning execution")

groupman = group_manager.GroupManager(BASE_DIR + "grades.csv")

# iterate through the folder, assigning a directory to each group
os.chdir(BASE_DIR)
sub_dirs = os.listdir()
groupman.restart()
while (groupman.has_next() == True):
    group = groupman.next()
    logger.info("====Starting to deal with group: {g}====".format(g=group.members))
    group_dirs = []
    for d in sub_dirs:
        directory_match = True 
        for stdnum in group.members:
            if stdnum.upper() not in d.upper():
                directory_match = False
        if directory_match == True:
             group_dirs.append(BASE_DIR + d)
    if len(group_dirs) == 0:
        logger.info("No submission found for: " + str(group.members))
        group.comment("No submissions for group.")
    elif len(group_dirs) == 1:
        group.comment("Directory \"{}\" assigned to group".format(str(group_dirs[0]), str(group.members)))
        if os.path.isdir(group_dirs[0] + "/Submission attachment(s)"):
            group.comment("Submission directory found. Proceeding.")
            group.directory = group_dirs[0]
            group.get_submissiontime()
            group.unzip_submission()
            group.find_src_file()
            #group.copy_src_to_centeral()
            group.prepend_stdnums()
            group.build_submission()
            group.run_tests()
        else:
            group.comment("No attachments found.")
        group.write_comments_file()
        group.clean()
    else:
        group.comment("This should never happen. Contact me.")

logger.info("Generating marks file")
groupman.generate_marks_file()

#### DEAD CODE #####
#groupman.restart()
#while (groupman.has_next() == True):
#    group = groupman.next()
#    print(str(group.members) + "  :  " + str(group.directory))

# for each group:
# take the submission and move it to a working directory. 
# read timestamp. Compute scaling factor
# assert compile and link
# pass .elf to "run tests"
# scale mark by factor
# pack mark and comment into a CSV
