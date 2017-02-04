#!/usr/bin/env python
#

#
# The MIT License (MIT)
# 
# Copyright (c) 2017 wak109
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import sys

from itertools import chain
from itertools import dropwhile
if sys.version_info < (3, 0):
    from itertools import ifilter
    from itertools import ifilterfalse
    from itertools import imap
from itertools import takewhile


if sys.version_info < (3, 2):

    def accumulate(iterable, func=operator.add):
        it = iter(iterable)
        try:
            total = next(it)
        except StopIteration:
            return
        yield total
        for element in it:
            total = func(total, element)
            yield total


def pairwise(iterable):
    iterator = iter(iterable)
    prev = next(iterator)
    for it in iterator:
        yield prev, it
        prev = it


def blockby_separator(predicate, iterable):
    block = []
    for it in iterable:
        if predicate(it):
            if block:
                yield block
            block = []
        else:
            block.append(it)
    if block:
        yield block


def blockby_header(predicate, iterable):
    block = None
    for it in iterable:
        if predicate(it):
            if block:
                yield block
            block = [it]
        elif block:
            block.append(it)
    if block:
        yield block
    

########################################################################
# main
########################################################################

if __name__ == '__main__':
    import unittest
    from test.iteratorext_test import *

    unittest.main(verbosity=2)
