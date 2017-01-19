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
import sys
import operator

from abc import ABCMeta, abstractmethod, abstractproperty
from itertools import chain

if sys.version_info >= (3, 0):
    from functools import reduce

def composer(obj, *args, **kwargs):

    def _nargs(func):
        def _len(x): return len(x) if x else 0
        _spec = inspect.getargspec(func)
        return _len(_spec.args) - _len(_spec.defaults)

    if args or kwargs:
        if callable(obj):
            return ComposerFunction(obj, *args, **kwargs)
        else:
            raise NotImplementedError()
    else:
        if isinstance(obj, ComposerBase):
            return obj
        elif isinstance(obj, int):
            return ComposerArgs(obj)
        elif isinstance(obj, str):
            return ComposerKwargs(obj)
        elif inspect.isfunction(obj):
            return ComposerFunction(obj, \
                    *(tuple([ ComposerArgs(idx) for idx in \
                    range(0, _nargs(obj)) ])))
        elif callable(obj): # callbale but not function
            return ComposerFunction(obj, \
                    *(tuple([ ComposerArgs(idx) for idx in \
                    range(0, _nargs(obj) - 1) ])))
        else:
            raise NotImplementedError()


class ComposerBase(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def getArgsSet(self):
        raise NotImplementedError()

    @abstractmethod
    def getKwargsSet(self):
        raise NotImplementedError()
        
    @abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError()


class ComposerFunctionBase(ComposerBase):

    @abstractmethod
    def applyArgs(self, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def run(self):
        raise NotImplementedError()

    @abstractmethod
    def __rshift__(self, func):
        raise NotImplementedError()

    def __call__(self, *args, **kwargs):
        func = self.applyArgs(*args, **kwargs)
        return func if len(func.getArgsSet()) != 0 or \
                len(func.getKwargsSet()) != 0 else func.run()


class ComposerArgs(ComposerBase):

    def __init__(self, idx):
        self.idx = idx

    def __call__(self, *args, **kwargs):
        return args[self.idx] if self.idx < len(args) else \
                ComposerArgs(self.idx - len(args))

    def getArgsSet(self):
        return (self.idx, )

    def getKwargsSet(self):
        return ()


class ComposerKwargs(ComposerBase):

    def __init__(self, key):
        self.key = key

    def __call__(self, *args, **kwargs):
         return kwargs[self.key] if self.key in kwargs else self

    def getArgsSet(self):
        return ()

    def getKwargsSet(self):
        return (self.key,)


class ComposerFunction(ComposerFunctionBase):

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def getArgsSet(self):
        return tuple(frozenset(reduce(operator.add, \
                [ arg.getArgsSet() for arg in chain( \
                self.args, self.kwargs.values()) \
                if isinstance(arg, ComposerBase) ], ())))

    def getKwargsSet(self):
        return tuple(frozenset(reduce(operator.add, \
                [arg.getKwargsSet() for arg in chain( \
                self.args, self.kwargs.values()) \
                if isinstance(arg, ComposerBase)], ())))
        

    def applyArgs(self, *args, **kwargs):

        def replaceArg(arg, *args, **kwargs):
            return arg(*args, **kwargs) if \
                    isinstance(arg, ComposerBase) else arg

        return ComposerFunction(self.func, \
            *(tuple([replaceArg(arg, *args, **kwargs) \
                for arg in self.args])), \
            **(dict([(key, replaceArg(value, *args, **kwargs)) \
                for key, value in self.kwargs.items() ])))

    def run(self):
        return self.func(*self.args, **self.kwargs)

    def __rshift__(self, outf):
        return ComposerBind(self, outf)


class ComposerBind(ComposerFunctionBase):

    def __init__(self, inf, outf):
        self.inf = inf
        self.outf = outf

    def getArgsSet(self):
        return self.inf.getArgsSet()

    def getKwargsSet(self):
        return tuple(frozenset(self.inf.getKwargsSet() + \
                self.outf.getKwargsSet()))


    def applyArgs(self, *args, **kwargs):
        return ComposerBind(self.inf.applyArgs(*args, **kwargs), \
            self.outf.applyArgs(**kwargs))

    def run(self):
        def force_tuple(x):
            return x if isinstance(x, tuple) else (x, )
        return self.outf(*force_tuple(self.inf.run()))

    def __rshift__(self, outf):
        return ComposerBind(self, outf)

########################################################################
# main
########################################################################

if __name__ == '__main__':
    import unittest
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), 'test'))
    from composer_test import *

    unittest.main(verbosity=2)
