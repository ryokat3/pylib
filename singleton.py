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

import inspect
import threading

class Singleton(type):

    def __new__(cls, name, bases, dic):
        dic['_instance'] = None
        dic['_instance_lock'] = threading.Lock()
        return type.__new__(cls, name, bases, dic)

    def __call__(self, *args, **kwargs):
        
        with self._instance_lock:
            if self._instance == None:
                self._instance = type.__call__(self, *args, **kwargs)
        return self._instance


class SingletonDict(type):

    def __new__(cls, name, bases, dic):
        dic['_init_func'] = dic.get('__init__') if '__init__' in dic else None
        dic['_instance_dict'] = {}
        dic['_instance_dict_lock'] = threading.Lock()
        return type.__new__(cls, name, bases, dic)


    def __call__(self, *args, **kwargs):
        if self._init_func != None:
            ignore = object()
            key = tuple(sorted([ (key, val) for key, val in \
                    inspect.getcallargs(self._init_func, \
                    ignore, *args, **kwargs).items() \
                    if val != ignore and \
                    ((hasattr(self, 'KEY_ARGS') and \
                    key in getattr(self, 'KEY_ARGS')) \
                    or not hasattr(self, 'KEY_ARGS'))]))
        else:
            key = ()
        with self._instance_dict_lock:
            if not key in self._instance_dict:
                self._instance_dict[key] = \
                        type.__call__(self, *args, **kwargs)
        return self._instance_dict[key]

########################################################################
# main
########################################################################

if __name__ == '__main__':
    import unittest
    import os
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), 'test'))
    from singleton_test import *

    unittest.main(verbosity=2)
