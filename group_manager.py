import csv
import logging
import time
import os
import subprocess
import elf_parser

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
                    self.groups.append(members, 
                                       group_id,
                                       base_dir,
                                       self.logger.getChild("group_{m}".format(m=members)))

    def __iter__(self):
        self.iter_pointer = 0
        return self

    def __next__(self):
        if self.group_pointer == len(self.groups):
            raise StopIteration
        self.group_pointer += 1
        return self.groups[self.group_pointer - 1]

    def generate_marks_file(self, csv_old, csv_new):
        rows =[]
        with open(csv_old) as fi:
            old_reader = csv.reader(fi)
            for row in old_reader:
                rows.append(row)

        for group in self.groups:
            group_row = None # this will be a reference to the group's row
            if group.directory is not None: # ensure they submitted with a valid directory
                for member in group.members:
                    for row_to_check in rows:
                        if (len(row_to_check) == 4) and (member in row_to_check[0]): # std num found in Group column
                            if group_row == None: # not yet assigned - assign directly
                                group_row = row_to_check
                            else: # already assigned - ensure new assignment matches old
                                if row_to_check is not group_row:
                                    raise Exception("Group {g} found in two rows. 1: {r1}. 2: {r2}".format(g=group.members, \
                                            r1 = group_row, r2 = row_to_check))
                if group_row == None:
                    raise Exception("Group {g} submitted but no matching row found".format(g = group.members))
                group_row[3] = group.mark # group_row should be a reference to a row in rows, so this should update rows.
        # write back        
        with open(csv_new, 'w') as fi:
            new_writer = csv.writer(fi)
            for row in rows:
                new_writer.writerow(row)


