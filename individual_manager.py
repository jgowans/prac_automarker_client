import csv
import logging
import time
import os
from individual import Individual

# A line from the grades file looks like:
#"Display ID","ID","Last Name","First Name","grade"
#"admjon006","admjon006","Adams","Jonathan","42"


class IndividualManager:
    def __init__(self, base_dir, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.individuals = []
        self.base_dir = base_dir
        self.create_individuals_from_grades()
        self.logger.info("individual creating completed with a total of {l} groups.".format(l=len(self.individuals)))

    def create_individuals_from_grades(self):
        with open(self.base_dir + '/grades.csv') as gradesfile:
            gradesfile_reader = csv.reader(gradesfile)
            for gradeline in gradesfile_reader:
                if (len(gradeline) == 5) and (gradeline[0] != 'Display ID'): # Valid grade line
                    user_id = gradeline[1]
                    self.groups.append(Individual(user_id
                                             self.logger.getChild("individual_{uid}".format(uid=user_id))))

    def __iter__(self):
        self.iter_pointer = 0
        return self

    def __next__(self):
        if self.iter_pointer == len(self.individuals):
            raise StopIteration
        self.iter_pointer += 1
        return self.individuals[self.iter_pointer - 1]

    def generate_marks_file(self, csv_old, csv_new):
        rows = []
        with open(csv_old) as fi:
            old_reader = csv.reader(fi)
            for row in old_reader:
                rows.append(row)
        for individual in self:
            for row_to_check in rows:
                if (len(row_to_check) == 4) and (individual.user_id == row_to_check[1]):
                        row_to_check[3] = individual.mark
                        break  # the mark has been assigned - get out of inner loop
        with open(csv_new, 'w') as fi:
            new_writer = csv.writer(fi)
            for row in rows:
                new_writer.writerow(row)
