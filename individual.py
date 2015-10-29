import logging
import zipfile
import shutil
import os
import time

class NoDirectoryForIndividual(Exception):
    pass
class IndividualSourceFileProblem(Exception):
    pass
class NoSourceFileFound(IndividualSourceFileProblem):
    pass
class MultipleSourceFilesFound(IndividualSourceFileProblem):
    pass
class IncorrectNumberOfZipsFound(IndividualSourceFileProblem):
    pass

class Individual:
    def __init__(self, user_id, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.user_id = user_id
        self.members = user_id
        self.mark = 0
        self.src_file = None

    def catalogue_submission_files(self):
        self.files = []
        self.files_for_plag_checking = []
        os.chdir(self.submission_directory)
        all_files = os.listdir()
        s_files = [fi for fi in all_files if fi.endswith(".s")]
        self.files += s_files
        makefiles = [fi for fi in all_files if fi.endswith("akefile")]
        self.files += makefiles

    def increment_mark(self, val):
        self.mark += val
        self.logger.info("Mark set to {m:.2}".format(m = float(self.mark)))

    def find_directories(self, base_dir):
        directories = os.listdir(base_dir)
        for directory in directories:
            if self.user_id in directory:
                self.directory = "{base}/{d}/".format(base = base_dir, d = directory)
                self.submission_directory = "{base}/Submission attachment(s)/".format(base = self.directory)
                self.logger.debug("Using dir: {d}".format(d = self.submission_directory))
                return
        raise NoDirectoryForGroup("No dir for individual: {uid}".format(uid = self.user_id))

    def unzip_submission(self):
        os.chdir(self.submission_directory)
        zip_files = [fi for fi in all_files if fi.endswith(".zip")]
        if len(zip_files) != 1:
            self.logger.critical("Too many or not enough zip file found out of: {a}. Aborting.".format(a = all_files))
            raise IncorrectNumberOfZipsFound()
        self.logger.info("Extracting zipfile: {z}".format(z = zip_files[0]))
        with zipfile.ZipFile(zip_files[0]) as z:
            z.extractall()
        self.delete_elfs()

    def prepend_stdnums(self):
        # iterate through all files_for_plagiarism and add a comment
        stdnum_str = "@ {m}\n".format(m = str(self.members))
        with open(self.submission_directory + self.src_file, "r") as f:
            src_code = f.read()
        with open(self.submission_directory + self.src_file, "w") as f:
            f.write(stdnum_str + src_code)

    def copy_files_to_common_dir(self, base):
        members = self.members.replace(' ', '_')
        destination_directory = base + '/' + members
        os.mkdir(destination_directory)
        for f in self.files_for_plag_check:
            source_path = "{base}/{src}".format(base = self.submission_directory, src = f)
            destination_path = "{d}/{f}".format(d = destination_directory, f = f)
            shutil.copyfile(source_path, destination_path)

    def get_submissiontime(self):
        with open(str(self.group_directory) + "/timestamp.txt") as timefile:
            timestamp = timefile.readline() # will return something like: '20140805211624959'
            self.submission_time = time.strptime(timestamp[0:14], "%Y%m%d%H%M%S") # prune off the miliseconds
            self.logger.info("Submissiontime of {} assigned".format(time.strftime("%a:%H:%M", self.submission_time)))
