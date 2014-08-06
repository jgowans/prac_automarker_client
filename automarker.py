#!/usr/bin/env python3

import os
import logging
import csv
import group_manager

BASE_DIR = "/tmp/Practical1/"

logging.basicConfig(level=logging.INFO, format="%(asctime)s:" + logging.BASIC_FORMAT)
logging.info("Automarker beginning execution")

#interface = interface_lib.InterrigatorInterface()

groupman = group_manager.GroupManager("/tmp/groups.csv")
# rename all submission folders to only be student numbers
#for old_dir in os.walk("/tmp/Practical1/").send(None)[1]:
#    new_dir = old_dir[old_dir.find('(') + 1 : old_dir.find(')')].upper()
#    os.rename("/tmp/Practical1/" + old_dir, "/tmp/Practical1/" + new_dir)

# iterate through the folder, assigning a directory to each group
os.chdir(BASE_DIR)
sub_dirs = os.listdir()
groupman.restart()
while (groupman.has_next() == True):
    group = groupman.next()
    group_dirs = []
    for d in sub_dirs:
        for stdnum in group.members:
            if d.find(stdnum.lower()) > 0:
                group_dirs.append(d)
    if len(group_dirs) == 0:
        logging.info("No submission found for: " + str(group.members))
        group.comment = "No submissions for group."
    elif len(group_dirs) == 1:
        logging.info("Directory : \"{}\" assigned to: {}".format(str(group_dirs[0]), str(group.members)))
        group.directory = BASE_DIR + group_dirs[0]
        group.get_submissiontime()
    else:
        logging.info("Multiple submissions for: {}".format(str(group.members)))
        group.comment = "Multiple submissions for group not marked."

groupman.restart()
while (groupman.has_next() == True):
    group = groupman.next()
    print(str(group.members) + "  :  " + str(group.directory))

# for each group:
# take the submission and move it to a working directory. 
# read timestamp. Compute scaling factor
# assert compile and link
# pass .elf to "run tests"
# scale mark by factor
# pack mark and comment into a CSV
