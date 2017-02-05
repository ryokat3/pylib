#!/usr/bin/env python
#

import unittest

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from iteratorext import *


class IteratorExtTest(unittest.TestCase):

    def test_pairwise(self):
        it = pairwise([1,2,3,4])
        self.assertEqual(next(it), (1,2))
        self.assertEqual(next(it), (2,3))
        self.assertEqual(next(it), (3,4))
        with self.assertRaises(StopIteration):
            next(it)

        it = pairwise([])
        with self.assertRaises(StopIteration):
            next(it)

    def test_blockby_separator(self):
        it = blockby_separator(lambda x: x == 0, [0,1,0,3,4,0])
        self.assertEqual(next(it), [1])
        self.assertEqual(next(it), [3,4])
        with self.assertRaises(StopIteration):
            next(it)

        it = blockby_separator(lambda x: x == 0, [])
        with self.assertRaises(StopIteration):
            next(it)

    def test_blockby_header(self):
        it = blockby_header(lambda x: x == 0, [0,1,0,3,4,0])
        self.assertEqual(next(it), [0,1])
        self.assertEqual(next(it), [0,3,4])
        self.assertEqual(next(it), [0])
        with self.assertRaises(StopIteration):
            next(it)

        it = blockby_header(lambda x: x == 0, [])
        with self.assertRaises(StopIteration):
            next(it)

########################################################################
# main
########################################################################

if __name__ == '__main__':
    unittest.main(verbosity=2)
