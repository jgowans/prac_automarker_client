#!/usr/bin/env python3

import os
import logging
import time
import argparse
from prac_tests import BuildFailedError
from group import Group, GroupSourceFileProblem
from prac3_tests import Prac3Tests

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter("%(asctime)s:" + logging.BASIC_FORMAT))
logger.addHandler(console_handler)

parser = argparse.ArgumentParser(description = "Individual prac runner")
parser.add_argument('--group_dir')
args = parser.parse_args()

group = Group(members = 'MEMBERS', 
              group_id = 'GROUP_ID',
              logger = logger.getChild('group'))
group.group_directory = args.group_dir
group.submission_directory = args.group_dir
group.delete_elfs()
group.find_src_file()
tester = Prac3Tests(group, logger.getChild('prac3'))
tester.build()
tester.run_tests()
