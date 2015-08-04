#!/usr/bin/env python3

PRACNUMBER = "1"

import os
import logging
import time
import csv
import group_manager

PRACNUMBER = 1

logger = logging.getLogger()
logfile_handler = logging.FileHandler(filename = "/tmp/prac{p}_{t}.log".format(
    p = PRACNUMBER, t = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())))
logfile_handler.setLevel(level=logging.DEBUG)
logfile_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
logger.addHandler(logfile_handler)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
logger.addHandler(console_handler)

BASE_DIR = "/tmp/Practical{p}/".format(p = PRACNUMBER)
COMMON_DIR = "/tmp/common_dir_{t}".format(t = time.strftime("%Y_%m_%d_%H_%M"))
os.mkdir(COMMON_DIR)
logger.info("Automarker beginning execution")

groupman = group_manager.GroupManager(base_dir)
for group in groupman:
    logfile_handler.setFormatter(logging.Formatter("%(asctime)s:" + group.members + ':' + logging.BASIC_FORMAT))
    console_handler.setFormatter(logging.Formatter("%(asctime)s:" + group.members + ':' + logging.BASIC_FORMAT))
    logger.info("====Starting to deal with group: {g}====".format(g=group.members))
    group_comment_logger = logging.FileHandler("{d}/comments.txt".format(d = group.group_directory), 'w')
    group_comment_logger.setFormatter('%(levelname)s:%(name)s:%(message)s')
    group_comment_logger.setLevel(logging.INFO)
    logger.addHandler(group_comment_logger)
    try:
        group.find_group_dir(BASE_DIR)
        group.delete_elfs()
        group.find_src_file()
        group.prepend_stdnums()
        group.copy_source_to_common_dir(COMMON_DIR)
        with Prac1Tests(group, logger.getChild('prac1')) as tests:
            tests.run_tests()
    except Exception as e:
        pass
    finally:
        group_comment_logger.close()
        logger.removeHandler(group_comment_logger)
        logger.debug("Closed and removed group handler")

logfile_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
console_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
logger.info("Generating marks file")
groupman.generate_marks_file("/tmp/Practical{p}/grades.csv".format(p = PRACNUMBER), \
        "/tmp/Practical{p}/grades_new.csv".format(p = PRACNUMBER))
