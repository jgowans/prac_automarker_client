#!/usr/bin/env python3

PRACNUMBER = 3

import importlib
import os
import logging
import time
import csv
#import group_manager
import individual_manager
from prac_tests import BuildFailedError, SourceFileProblem

tester_module = importlib.import_module("prac_exam_2_part_{n}_tests".format(n = PRACNUMBER))
TesterClass = getattr(tester_module, "PracExam2Part{n}Tests".format(n = PRACNUMBER))

logger = logging.getLogger()
logfile_handler = logging.FileHandler(filename = "/tmp/prac_exam_2_part_{p}_{t}.log".format(
    p = PRACNUMBER, t = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())))
logger.setLevel(logging.DEBUG)
logfile_handler.setLevel(level=logging.DEBUG)
logfile_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
logger.addHandler(logfile_handler)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
logger.addHandler(console_handler)

BASE_DIR = "/tmp/Practical Exam 2 Part {p}/".format(p = PRACNUMBER)
COMMON_DIR = "/tmp/prac_exam_2_part{n}_common_dir_{t}".format(n = PRACNUMBER, t = time.strftime("%Y_%m_%d_%H_%M_%S"))
os.mkdir(COMMON_DIR)
logger.info("Automarker beginning execution")

indivman = individual_manager.IndividualManager(BASE_DIR)
for submitter in indivman:
    submitter.find_directories(BASE_DIR)
    logfile_handler.setFormatter(logging.Formatter("%(asctime)s:" + submitter.members + ':' + logging.BASIC_FORMAT))
    console_handler.setFormatter(logging.Formatter("%(asctime)s:" + submitter.members + ':' + logging.BASIC_FORMAT))
    logger.info("====Starting to deal with submitter: {s}====".format(s = submitter.members))
    comment_logger = logging.FileHandler("{d}/comments.txt".format(d = submitter.directory), 'w')
    comment_logger.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s<br>'))
    comment_logger.setLevel(logging.INFO)
    logger.addHandler(comment_logger)
    try:
        tester =  TesterClass(submitter, logger.getChild('part{n}'.format(n = PRACNUMBER)))
        tester.unzip_submission()
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
indivman.generate_marks_file("{b}/grades.csv".format(b = BASE_DIR), \
        "{b}/grades_new.csv".format(b = BASE_DIR))
