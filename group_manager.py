import csv
import logging
import time
import os
from group import Group

# A line from the grades file looks like:
# Group,ID,Users,grade
#KXXDOY001 SMTJER002,40ad3cd6-a512-4b14-9e30-a909d2e762cf,Do Yeou Ku; Jeremy Smith, <grade goes here>

class GroupManager:
    def __init__(self, base_dir, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.groups = []
        self.create_groups_from_grades()
        self.logger.info("group creating completed with a total of {groupnums} groups.".format(groupnums=len(self.groups)))

    def create_groups_from_grades(self):
        with open(self.base_dir + '/grades.csv') as gradesfile:
            gradesfile_reader = csv.reader(gradesfile)
            for gradeline in gradesfile_reader:
                if len(gradeline) == 4: # Valid grade line
                    members = gradeline[0]
                    group_id = gradeline[1]
                    self.groups.append(Group(members,
                                             group_id,
                                             base_dir,
                                             self.logger.getChild("group".format(m=members))))

    def __iter__(self):
        self.iter_pointer = 0
        return self

    def __next__(self):
        if self.iter_pointer == len(self.groups):
            raise StopIteration
        self.group_pointer += 1
        return self.groups[self.iter_pointer - 1]

    def generate_marks_file(self, csv_old, csv_new):
        rows = []
        with open(csv_old) as fi:
            old_reader = csv.reader(fi)
            for row in old_reader:
                rows.append(row)
        for group in self:
            for row_to_check in rows:
                if (len(row_to_check) == 4) and (group.group_id == row_to_check[1]):
                        group_row[3] = group.mark 
                        break  # the mark has been assigned - get out of inner loop
        with open(csv_new, 'w') as fi:
            new_writer = csv.writer(fi)
            for row in rows:
                new_writer.writerow(row)
