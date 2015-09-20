#!/usr/bin/env python3

import os
import logging
import time
import argparse
import re
from individual import Individual
#from prac3_tests import Prac3Tests
from prac_exam_0_tests import PracExam0Tests

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
submitter.catalogue_submission_files()
tester = PracExam0Tests(submitter, logger.getChild('prac3'))
tester.build()
tester.run_tests()
