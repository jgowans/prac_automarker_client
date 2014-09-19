#!/usr/bin/env python3

PRACNUMBER = "5"

import os
import logging
import time
logging.basicConfig(filename = "/tmp/prac{p}_{t}.log".format(p = PRACNUMBER, t = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())), \
        level=logging.INFO, format="%(asctime)s:" + logging.BASIC_FORMAT)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
logging.getLogger('').addHandler(console)
logger = logging.getLogger(__name__)
import csv
import group_manager

BASE_DIR = "/tmp/Practical{p}/".format(p = PRACNUMBER)

logger.info("Automarker beginning execution")


groupman = group_manager.GroupManager("/tmp/groups.csv")

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
            if stdnum not in d.upper():
                directory_match = False
        if directory_match == True:
             group_dirs.append(BASE_DIR + d)
    if len(group_dirs) == 0:
        logger.info("No submission found for: " + str(group.members))
        group.comment("No submissions for group.")
    elif len(group_dirs) == 1:
        group.comment("Directory \"{}\" assigned to group".format(str(group_dirs[0]), str(group.members)))
        group.comment("Submission directory from one group member found. Proceeding.")
        group.directory = group_dirs[0]
        group.get_submissiontime()
        group.find_src_file()
        group.build_submission()
        group.run_tests()
        group.write_comments_file()
        group.clean()
    else:
        group.comment("This should never happen. Contact me.")

logger.info("Generating marks file")
groupman.generate_marks_file("/tmp/Practical{p}/grades.csv".format(p = PRACNUMBER), \
        "/tmp/Practical{p}/grades_new.csv".format(p = PRACNUMBER))

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
