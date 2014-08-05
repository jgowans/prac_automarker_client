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
    group_dir = None
    for d in sub_dirs:
        for stdnum in group.members:
            if d.find(stdnum.lower()) >= 0:
                if group_dir is None:
                    group_dir = d
                else:
                    group_dir = None
                    groupman.set_comment(groupnum, "Multiple submissions not marked")
    group.directory = BASE_DIR + group_dir


    #groupman.set_dir(groupnum, 
        # try match a dir for member 1
    #    if d.find(stdnums[
    # try match a dir for member 2
    # if two dirs defined:
        # comment = multiple submissions, mark = 0
    # if no dirs, do nothing
    # if only one dir, assign to group

# for each group:
# assert that only one member has submitted.
# if multiple submissions, assign 0 to the group.
# take the submission and move it to a working directory. 
# read timestamp. Compute scaling factor
# assert compile and link
# pass .elf to "run tests"
# scale mark by factor
# pack mark and comment into a CSV
