#!/usr/bin/env python3

import os
import logging
import time
import csv
#import group_manager
import individual_manager
from prac_tests import BuildFailedError
#from group import GroupSourceFileProblem
from prac_exam_0_tests import PracExam0Tests

PRACNUMBER = None

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

#BASE_DIR = "/tmp/Practical{p}/".format(p = PRACNUMBER)
BASE_DIR = "/tmp/Practical Exam 0"
COMMON_DIR = "/tmp/common_dir_{t}".format(t = time.strftime("%Y_%m_%d_%H_%M_%S"))
os.mkdir(COMMON_DIR)
logger.info("Automarker beginning execution")

indivman = individual_manager.IndividualManager(BASE_DIR)
for student in indivman:
    student.find_directories(BASE_DIR)
    logfile_handler.setFormatter(logging.Formatter("%(asctime)s:" + student.user_id + ':' + logging.BASIC_FORMAT))
    console_handler.setFormatter(logging.Formatter("%(asctime)s:" + student.user_id + ':' + logging.BASIC_FORMAT))
    logger.info("====Starting to deal with student: {uid}====".format(uid = student.user_id))
    comment_logger = logging.FileHandler("{d}/comments.txt".format(d = student.directory), 'w')
    comment_logger.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s<br>'))
    comment_logger.setLevel(logging.INFO)
    logger.addHandler(comment_logger)
    try:
        student.catalogue_submission_files()
        #group.prepend_stdnums()
        #group.copy_source_to_common_dir(COMMON_DIR)
        tester =  PracExam0Tests(student, logger.getChild('pt0'))
        tester.build()
        tester.run_tests()
    except BuildFailedError as e:
        logger.critical("Build Failed. Exiting")
    finally:
        comment_logger.close()
        logger.removeHandler(comment_logger)
        logger.debug("Closed and removed comment_logger handler")

logfile_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
console_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
logger.info("Generating marks file")
indivman.generate_marks_file("/tmp/Practical Exam 0/grades.csv", \
        "/tmp/Practical Exam 0/grades_new.csv")
