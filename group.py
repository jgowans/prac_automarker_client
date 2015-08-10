import logging
import zipfile
import shutil
import os

class NoDirectoryForGroup(Exception):
    pass
class GroupSourceFileProblem(Exception):
    pass
class NoSourceFileFound(GroupSourceFileProblem):
    pass
class MultipleSourceFilesFound(GroupSourceFileProblem):
    pass
class IncorrectNumberOfZipsFound(GroupSourceFileProblem):
    pass

class Group:
    def __init__(self, members, group_id, base_dir, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.members = members
        self.group_id = group_id
        self.mark = 0
        self.src_file = None

    def find_group_dir(self, base_dir):
        directories = os.listdir(base_dir)
        for directory in directories:
            if self.group_id in directory:
                self.group_directory = "{base}/{d}/".format(base = base_dir, d = directory)
                self.submission_directory = "{base}/Submission attachment(s)/".format(base = self.group_directory)
                self.logger.debug("Using dir: {d}".format(d = self.submission_directory))
                return
        raise NoDirectoryForGroup("No dir for members: {m}, id: {gid}".format(m = self.members, gid = self.group_id))

    def delete_elfs(self):
        os.chdir(self.submission_directory)
        all_files = os.listdir()
        elf_files = [fi for fi in all_files if fi.endswith(".elf")]
        if len(elf_files) > 0:
            self.logger.debug("Elf files exist before building: {e}".format(e = elf_files))
            for elf in elf_files:
                os.remove(elf)
            self.logger.debug("Elf files deleted")
    
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

    def find_src_file(self):
        os.chdir(self.submission_directory)
        all_files = os.listdir()
        assembly_files = [fi for fi in all_files if fi.endswith(".s")]
        if len(assembly_files) == 1:
            self.src_file = assembly_files[0]
            self.logger.info("Only 1 .s file submitted, namely: {}".format(self.src_file))
        elif len(assembly_files) > 1:
            self.logger.critical("Multiple .s files. Not sure which to mark. Aborting")
            raise MultipleSourceFilesFound()
        else:
            self.logger.critical("No suitable source file found out of: {fi}".format(fi = all_files))
            raise NoSourceFileFound()

    def prepend_stdnums(self):
        stdnum_str = "@ {m}\n".format(m = str(self.members))
        with open(self.submission_directory + self.src_file, "r") as f:
            src_code = f.read()
        with open(self.submission_directory + self.src_file, "w") as f:
            f.write(stdnum_str + src_code)

    def copy_source_to_common_dir(self, directory):
        members = self.members.replace(' ', '_')
        file_name = "{m}.s".format(m = members)
        source_path = "{base}/{src}".format(base = self.submission_directory, src = self.src_file)
        destination_path = "{d}/{f}".format(d = directory, f = file_name)
        shutil.copyfile(source_path, destination_path)
