#!/usr/bin/env python3

import importlib
import os
import logging
import time
import argparse
import re
from group import Group

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
logger.addHandler(console_handler)

parser = argparse.ArgumentParser(description = "Group prac runner")
parser.add_argument('-d')
parser.add_argument('-p')
args = parser.parse_args()

tester_module = importlib.import_module("prac{n}_tests".format(n =  args.p))
TesterClass = getattr(tester_module, "Prac{n}Tests".format(n = args.p))

student_numbers = ""
for match in re.finditer("[a-z]{6}[0-9]{3}", args.d.lower()):
    student_numbers += match.group(0) + '_'
student_numbers = student_numbers[0:-2]
submitter = Group(members = student_numbers, group_id=student_numbers, logger = logger.getChild('manual_marker'))
submitter.directory = args.d
submitter.submission_directory = args.d
tester = TesterClass(submitter, logger.getChild('prac{n}'.format(n = args.p)))
tester.catalogue_submission_files()
tester.build()
tester.run_tests()
