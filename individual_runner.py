#!/usr/bin/env python3

import os
import logging
import time
import argparse
from prac_tests import BuildFailedError
from group import Group, GroupSourceFileProblem
from prac2_tests import Prac2Tests

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
logger.addHandler(console_handler)

aparser = argparse.ArgumentParser(description = "Individual prac runner")
parser.add_argument('--group_dir')
args = parser.parse_args()

group = Group(members = 'MEMBERS', 
              group_id = 'GROUP_ID',
              logger = logger.getChild('group'))
group.group_directory = args.group_dir
group.submission_directory = "{base}/Submission attachment(s)/".format(base = group.group_directory)
group.delete_elfs()
group.find_src_file()
tester = Prac2Tests(group, logger.getChild('prac2'))
tester.build()
tester.run_tests()
