#!/usr/bin/env ipy
#

import clr
clr.AddReference("System.Windows.Forms")

from System.Windows import Forms
from System.Windows.Forms import MessageBox

import operator
import os
import sys
import tempfile
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from comproxy import *
from test_utils import *


def kill_winproc (process_name):
    '''Kill a process in Windows'''
    try:
        killed = os.system('c:\Windows\System32\tskill.exe ' + process_name)
    except Exception, e:
        killed = 0
    return killed


class ExcelApplicationUnitTest(unittest.TestCase):

    def setUp(self):
        if find_excel() != None:
            MessageBox.Show("Close Excel", "WARNING")
            kill_winproc('excel')

    def test_start_excel(self):
        self.assertFalse(find_excel())
        self.assertTrue(start_excel())
        self.assertTrue(find_excel())

    
########################################################################
# Main
########################################################################

if __name__ == '__main__':
    import logging
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    unittest.main(verbosity=2)
