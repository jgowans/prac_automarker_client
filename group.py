import logging
import zipfile

class NoDirectoryForGroup(Exception):
    pass
class NoSourceFileFound(Exception):
    pass

class Group:
    def __init__(self, members, group_id, base_dir, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.members = members
        self.comment_arr = []
        self.mark = 0
        self.src_file = None
        self.group_directory = self.find_group_dir(base_dir, group_id)
        self.submission_directory = "{base}/Submission attachment(s)/".format(base = self.group_directory)
        self.delete_elfs()

    def find_group_dir(self, base_dir, group_id):
        directories = os.listdir(base_dir)
        for directory in directories:
            if group_id in directory:
                return "{base}/{d}/".format(base = base_dir, d = directory)
        raise NoDirectoryForGroup

    def comment(self, to_append):
        logger.info(to_append)
        self.comment_arr.append(str(to_append))

    def delete_elfs(self):
        os.chdir(self.submission_directory)
        all_files = os.listdir()
        elf_files = [fi for fi in all_files if fi.endswith(".elf")]
        if len(elf_files) > 0:
            self.comment("Elf files exist before unzipping run: {e}".format(e = elf_files))
            for elf in elf_files:
                os.remove(elf)
            self.comment("Elf files deleted")
    
    def unzip_submission(self):
        os.chdir(self.submission_directory)
        zip_files = [fi for fi in all_files if fi.endswith(".zip")]
        if len(zip_files) != 1:
            self.comment("Too many or not enough zip file found out of: {a}".format(a = all_files))
            self.comment("Aborting.")
            return False
        self.comment("Extracting zipfile: {z}".format(z = zip_files[0]))
        with zipfile.ZipFile(zip_files[0]) as z:
            z.extractall()
        self.delete_elfs()

    def find_src_file(self):
        '''The matchin process is to 
        - first check for a main.s file
        - if not found, check if only 1 file submitted
        - if multiple files submitted, check if only one ends in a .s extension'''
        os.chdir(self.directory + "/Submission attachment(s)/")
        all_files = os.listdir()
        assembly_files = [fi for fi in all_files if fi.endswith(".s")]
        if len(assembly_files) == 1:
            self.src_file = assembly_files[0]
            self.comment("Only 1 .s file submitted, namely: {}".format(self.src_file))
        else:
            self.comment("No suitable source file found out of: {fi}".format(fi = all_files))
            raise NoSourceFileFound()

    def prepend_stdnums(self):
        stdnum_str = "@ {m}\n".format(m = str(self.members))
        with open(self.directory + "/Submission attachment(s)/" + self.src_file, "r") as f:
            src_code = f.read()
        with open(self.directory + "/Submission attachment(s)/" + self.src_file, "w") as f:
            f.write(stdnum_str + src_code)

    def copy_source_to_common_dir(self, directory):
        file_name = "{m0}_{m1}".format(m0 = self.members[0],
                                       m1 = self.members[1])
        source_path = "{base}/

    def build_submission(self):
        if self.src_file == None:
            self.comment("Can't build - no source file")
            return False
        self.comment("Attempting to compile file: {}".format(self.src_file))
        self.test_runner = prac10.Prac10Tests(self.comment, self.directory + "/Submission attachment(s)/", self.src_file)
        if self.test_runner.build() == False:
            self.test_runner = None

    def run_tests(self):
        if self.test_runner == None:
            self.comment("Can't run tests as no elf exists")
            self.mark = 0
        else:
            self.comment("Starting to run tests")
            # would probably be better to do this with inheretance... 
            self.mark = self.test_runner.run_tests()
            self.comment("Returned from running tests")

    def write_comments_file(self):
        with open(self.directory + "/comments.txt", "w") as f:
            for c in self.comment_arr:
                f.write(c + "<br>\n")
