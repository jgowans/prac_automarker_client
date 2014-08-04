#!/usr/bin/env python3

import os
import logging
import csv
import group_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s:" + logging.BASIC_FORMAT)
logging.info("Automarker beginning execution")

#interface = interface_lib.InterrigatorInterface()

groupman = group_manager.GroupManager("/tmp/groups.csv")

# rename all submission folders to only be student numbers
for old_dir in os.walk("/tmp/Practical1/").send(None)[1]:
    new_dir = old_dir[old_dir.find('(') + 1 : old_dir.find(')')].upper()
    os.rename("/tmp/Practical1/" + old_dir, "/tmp/Practical1/" + new_dir)

# for each group:
# assert that only one member has submitted.
# if multiple submissions, assign 0 to the group.
# take the submission and move it to a working directory. 
# read timestamp. Compute scaling factor
# assert compile and link
# pass .elf to "run tests"
# scale mark by factor
# pack mark and comment into a CSV
