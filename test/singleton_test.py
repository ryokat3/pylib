#!/usr/bin/env python
#

import operator
import unittest

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from singleton import *

class SingletonTest(unittest.TestCase):

    def test1(self):

        class Test(Singleton('Test', (object,), {})):

            def __init__(self, val):
                self.val = val

        inst1 = Test(1)
        inst2 = Test(2)

        self.assertEqual(inst1.val, 1)
        self.assertEqual(inst2.val, 1)

########################################################################
# main
########################################################################

if __name__ == '__main__':
    unittest.main(verbosity=2)
