#!/usr/bin/env python
#

import operator
import unittest

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from socket_select import *

class SocketSelectTest(unittest.TestCase):

    def test(self):
        pass

########################################################################
# main
########################################################################

if __name__ == '__main__':
    unittest.main(verbosity=2)
