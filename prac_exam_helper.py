from prac_exam_wed import PracExamWedTests
from prac_exam_thu import PracExamThuTests
import os

def w(dir):
    a = PracExamWedTests(print, dir, "main.c")
    try:                             
        os.remove(dir + "/main.elf")
    except:              
        pass             
    if a.build() == True:
        a.run_tests()


def t(dir):
    a = PracExamThuTests(print, dir, "main.c")
    try:                             
        os.remove(dir + "/main.elf")
    except:              
        pass             
    if a.build() == True:
        a.run_tests()
