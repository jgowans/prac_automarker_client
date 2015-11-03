#!/usr/bin/env python3

import importlib
import os
import logging
import time
import argparse
import re
from individual import Individual


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
logger.addHandler(console_handler)

parser = argparse.ArgumentParser(description = "Individual prac runner")
parser.add_argument('-d')
parser.add_argument('-p')
args = parser.parse_args()
part = args.p
user_id = re.search("([a-z]){6}([0-9]){3}", args.d).group(0)
submitter = Individual(user_id = user_id,
              logger = logger.getChild('manual_marker'))
submitter.directory = args.d
submitter.submission_directory = args.d

tester_module = importlib.import_module("prac_exam_2_part_{n}_tests".format(n = part))
TesterClass = getattr(tester_module, "PracExam2Part{n}Tests".format(n = part))
#tester_module = importlib.import_module("prac_exam_0_tests".format(n = part))
#TesterClass = getattr(tester_module, "PracExam0Tests".format(n = part))

tester = TesterClass(submitter, logger.getChild('pe1'))
tester.catalogue_submission_files()
tester.build()
tester.run_tests()
logger.info("Final Mark: {m:g}".format(m = float(submitter.mark)))
