#!/usr/bin/env python3

import os
import logging
import time
import csv
import group_manager
from prac_tests import BuildFailedError
from group import GroupSourceFileProblem
from prac3_tests import Prac3Tests

PRACNUMBER = 3

logger = logging.getLogger()
logfile_handler = logging.FileHandler(filename = "/tmp/prac{p}_{t}.log".format(
    p = PRACNUMBER, t = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())))
logger.setLevel(logging.DEBUG)
logfile_handler.setLevel(level=logging.DEBUG)
logfile_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
logger.addHandler(logfile_handler)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
logger.addHandler(console_handler)

BASE_DIR = "/tmp/Practical{p}/".format(p = PRACNUMBER)
COMMON_DIR = "/tmp/common_dir_{t}".format(t = time.strftime("%Y_%m_%d_%H_%M_%S"))
os.mkdir(COMMON_DIR)
logger.info("Automarker beginning execution")

groupman = group_manager.GroupManager(BASE_DIR)
for group in groupman:
    group.find_group_dir(BASE_DIR)
    logfile_handler.setFormatter(logging.Formatter("%(asctime)s:" + group.members + ':' + logging.BASIC_FORMAT))
    console_handler.setFormatter(logging.Formatter("%(asctime)s:" + group.members + ':' + logging.BASIC_FORMAT))
    logger.info("====Starting to deal with group: {g}====".format(g=group.members))
    group_comment_logger = logging.FileHandler("{d}/comments.txt".format(d = group.group_directory), 'w')
    group_comment_logger.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s<br>'))
    group_comment_logger.setLevel(logging.INFO)
    logger.addHandler(group_comment_logger)
    try:
        group.delete_elfs()
        group.find_src_file()
        group.prepend_stdnums()
        group.copy_source_to_common_dir(COMMON_DIR)
        tester =  Prac3Tests(group, logger.getChild('prac{n}'.format(n = PRACNUMBER)))
        tester.build()
        tester.run_tests()
    except BuildFailedError as e:
        logger.critical("Build Failed. Exiting")
    except GroupSourceFileProblem as e:
        logger.critical("Could not assigned a source file. Exiting")
    finally:
        group_comment_logger.close()
        logger.removeHandler(group_comment_logger)
        logger.debug("Closed and removed group handler")

logfile_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
console_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
logger.info("Generating marks file")
groupman.generate_marks_file("/tmp/Practical{p}/grades.csv".format(p = PRACNUMBER), \
        "/tmp/Practical{p}/grades_new.csv".format(p = PRACNUMBER))
