#!/usr/bin/env python3

PRACNUMBER = 1

import importlib
import os
import logging
import time
import argparse
import re
from individual import Individual

tester_module = importlib.import_module("prac_exam_1_part_{n}_tests".format(n = PRACNUMBER))
TesterClass = getattr(tester_module, "PracExam1Part{n}Tests".format(n = PRACNUMBER))


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
logger.addHandler(console_handler)

parser = argparse.ArgumentParser(description = "Individual prac runner")
parser.add_argument('-d')
args = parser.parse_args()
user_id = re.search("([a-z]){6}([0-9]){3}", args.d).group(0)
submitter = Individual(user_id = user_id,
              logger = logger.getChild('manual_marker'))
submitter.directory = args.d
submitter.submission_directory = args.d
tester = TesterClass(submitter, logger.getChild('prac3'))
tester.catalogue_submission_files()
tester.build()
tester.run_tests()
