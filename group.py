import logging
import zipfile
import shutil
import os
import time

class NoDirectoryForGroup(Exception):
    pass

class Group:
    def __init__(self, members, group_id, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.members = members
        self.group_id = group_id
        self.mark = 0
        self.src_file = None

    def increment_mark(self, val):
        self.mark += val
        self.logger.info("Mark set to {m}".format(m = self.mark))

    def find_directories(self, base_dir):
        directories = os.listdir(base_dir)
        for directory in directories:
            if self.group_id in directory:
                self.directory = "{base}/{d}/".format(base = base_dir, d = directory)
                self.submission_directory = "{base}/Submission attachment(s)/".format(base = self.directory)
                self.logger.debug("Using dir: {d}".format(d = self.submission_directory))
                return
        raise NoDirectoryForGroup("No dir for members: {m}, id: {gid}".format(m = self.members, gid = self.group_id))

    def copy_files_to_common_dir(self, base):
        members = self.members.replace(' ', '_')
        destination_directory = base + '/' + members
        os.mkdir(destination_directory)
        for f in self.files_for_plag_check:
            source_path = "{d}/{f}".format(
                d = self.submission_directory, f = f)
            destination_path = "{d}/{f}".format(
                d = destination_directory, f = f)
            shutil.copyfile(source_path, destination_path)

    def get_submissiontime(self):
        with open(str(self.group_directory) + "/timestamp.txt") as timefile:
            timestamp = timefile.readline() # will return something like: '20140805211624959'
            self.submission_time = time.strptime(timestamp[0:14], "%Y%m%d%H%M%S") # prune off the miliseconds
            self.logger.info("Submissiontime of {} assigned".format(time.strftime("%a:%H:%M", self.submission_time)))
