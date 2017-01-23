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
        dic['__instance__'] = None
        dic['__instance_lock__'] = threading.Lock()
        return type.__new__(cls, name, bases, dic)

    def __call__(self, *args, **kwargs):
        
        with self.__instance_lock__:
            if self.__instance__ == None:
                self.__instance__ = type.__call__(self, *args, **kwargs)
        return self.__instance__


class ParameterizedSingleton(type):

    def __new__(cls, name, bases, dic):
        # TODO: How can I get mangled '__init__' 
        dic['__init_func__'] = None
        for key, value in dic.items():
            if key == '__init__':
                dic['__init_func__'] = value
                break
        dic['__instance_dict__'] = {}
        dic['__instance_dict_lock__'] = threading.Lock()
        return type.__new__(cls, name, bases, dic)


    def __call__(self, *args, **kwargs):
        if self.__init_func__ != None:
            key = tuple(inspect.getcallargs(self.__init_func__, \
                    self, *args, **kwargs).items()[1:])
        else:
            key = ()
        with self.__instance_dict_lock__:
            if not key in self.__instance_dict__:
                self.__instance_dict__[key] = \
                        type.__call__(self, *args, **kwargs)
        return self.__instance_dict__[key]

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
