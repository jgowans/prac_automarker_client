import csv
import logging

class GroupManager:
    def __init__(self, filename):
        logging.info("initialising a groups manager")
        self.groups = {} # a dict mapping a group number to a list of stdnums
        self.marks = {} # a dict relating group number to their marks
        self.comments = {} # a dict relating group number to their comments
        self.submission_time = {} # group num to submission date time
        self.group_pointer = 0
        with open(filename) as groupsfile:
            groupsfile_reader = csv.reader(groupsfile, delimiter=',')
            for group in groupsfile_reader:
                # prune all empty members, then initialise the marks and comments dicts
                if group.count('') == 1:
                    group.remove('')
                self.groups[self.group_pointer] = group
                self.marks[self.group_pointer] = -1
                self.comments[self.group_pointer] = "Undefined."
                self.group_pointer += 1
        self.group_pointer = 0
        logging.info("group creating completed with a total of {groupnums} groups.".format(groupnums=len(self.groups)))

    def has_next(self):
        if self.group_pointer < len(self.groups):
            return True
        return False

    def next(self):
        if self.group_pointer == len(self.groups):
            logging.error("tried to acces group after no more groups")
            raise Exception
        self.group_pointer += 1
        return self.group_pointer - 1

    def get_members(self, groupnum):
        return self.groups[groupnum]

    def set_mark(self, groupnum, mark):
        self.marks[group] = mark

    def set_comment(self, groupnum, comment):
        self.comments[group] = comment

    def set_submission_time(self, groupnum, time):
        # probably have to do processing to convert Vula timestamp to something more meaningful
        self.submission_time[groupnum] = time

    def get_submission_time(self, groupnum):
        return self.submission_time[groupnum]

    def generate_output():
        pass




