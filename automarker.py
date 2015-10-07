#!/usr/bin/env python3

PRACNUMBER = 7

import importlib
import os
import logging
import time
import csv
import group_manager
#import individual_manager
from prac_tests import BuildFailedError, SourceFileProblem

tester_module = importlib.import_module("prac{n}_tests".format(n = PRACNUMBER))
TesterClass = getattr(tester_module, "Prac{n}Tests".format(n = PRACNUMBER))


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
for submitter in groupman:
    submitter.find_directories(BASE_DIR)
    logfile_handler.setFormatter(logging.Formatter("%(asctime)s:" + submitter.members + ':' + logging.BASIC_FORMAT))
    console_handler.setFormatter(logging.Formatter("%(asctime)s:" + submitter.members + ':' + logging.BASIC_FORMAT))
    logger.info("====Starting to deal with submitter: {s}====".format(s = submitter.members))
    comment_logger = logging.FileHandler("{d}/comments.txt".format(d = submitter.directory), 'w')
    comment_logger.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s<br>'))
    comment_logger.setLevel(logging.INFO)
    logger.addHandler(comment_logger)
    try:
        tester =  TesterClass(submitter, logger.getChild('prac{n}'.format(n = PRACNUMBER)))
        tester.catalogue_submission_files()
        submitter.copy_files_to_common_dir(COMMON_DIR)
        tester.build()
        tester.run_tests()
    except SourceFileProblem as e:
        logger.critical("Problem with source files. Exiting")
    except BuildFailedError as e:
        logger.critical("Build Failed. Exiting")
    finally:
        comment_logger.close()
        logger.removeHandler(comment_logger)
        logger.debug("Closed and removed comment_logger handler")

logfile_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
console_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
logger.info("Generating marks file")
groupman.generate_marks_file("/tmp/Practical{p}/grades.csv".format(p = PRACNUMBER), \
        "/tmp/Practical{p}/grades_new.csv".format(p = PRACNUMBER))
