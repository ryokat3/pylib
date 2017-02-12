import inspect
import os
import sys

def getTestFileName(filename):
    tmpdir = os.path.join(os.path.dirname(__file__), 'tmp')
    if not os.path.isdir(tmpdir):
        os.mkdir(tmpdir)
    testfile = os.path.join(tmpdir, filename)
    if os.path.isfile(testfile):
        os.remove(testfile)
    return testfile
