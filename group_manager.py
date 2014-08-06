import csv
import logging
import time

class Group:
    def __init__(self, members):
        self.members = members
        self.comment = "Undefined"
        self.directory = None
        self.mark = -1
        self.submissiontime = None
    
    def get_submissiontime(self):
        with open(str(self.directory) + "/timestamp.txt") as timefile:
            timestamp = timefile.readline() # will return something like: '20140805211624959'
            self.submissiontime = time.strptime(timestamp[0:14], "%Y%m%d%H%M%S") # prune off the miliseconds
            logging.info("Submissiontime of {} assigned to {}".format(time.strftime("%a:%H:%M", self.submissiontime), str(self.members)))

class GroupManager:
    def __init__(self, filename):
        logging.info("initialising a groups manager")
        self.groups = [] # a dict mapping a group number to a list of stdnums
        self.group_pointer = 0
        with open(filename) as groupsfile:
            groupsfile_reader = csv.reader(groupsfile, delimiter=',')
            for group in groupsfile_reader:
                # prune all empty members, then initialise the marks and comments dicts
                if group.count('') == 1:
                    group.remove('')
                self.groups.append(Group(group))
        logging.info("group creating completed with a total of {groupnums} groups.".format(groupnums=len(self.groups)))

    def has_next(self):
        if self.group_pointer < len(self.groups):
            return True
        return False

    def restart(self):
        self.group_pointer = 0

    def next(self):
        if self.group_pointer == len(self.groups):
            logging.error("tried to acces group after no more groups")
            raise Exception
        self.group_pointer += 1
        return self.groups[self.group_pointer - 1]

    def generate_output():
        pass




