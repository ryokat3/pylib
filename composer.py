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

try:
    from functools import reduce
except ImportError:
    pass

try:
    from itertools import imap
except ImportError:
    imap=map


def force_tuple(x):
    return x if isinstance(x, tuple) else (x, )


def get_nargs(func):
    def _len(x): return len(x) if x else 0
    _spec = inspect.getargspec(func)
    return _len(_spec.args) - _len(_spec.defaults)


def composer(obj, *args, **kwargs):

    if args or kwargs:
        if inspect.isgeneratorfunction(obj):
            return ComposerIterableFunction(obj, *args, **kwargs)
        elif callable(obj):
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
        elif inspect.isbuiltin(obj):
            return ComposerBuiltin(obj)
        elif inspect.isgeneratorfunction(obj):
            return ComposerIterableFunction(obj, \
                    *(tuple([ ComposerArgs(idx) for idx in \
                    range(0, get_nargs(obj)) ])))
        elif inspect.isfunction(obj):
            return ComposerFunction(obj, \
                    *(tuple([ ComposerArgs(idx) for idx in \
                    range(0, get_nargs(obj)) ])))
        elif inspect.ismethod(obj): # classmethod
            return ComposerFunction(obj, \
                    *(tuple([ ComposerArgs(idx) for idx in \
                    range(0, get_nargs(obj) - 1) ])))
        elif callable(obj): # callbale but not function nor method
            return ComposerFunction(obj, \
                    *(tuple([ ComposerArgs(idx) for idx in \
                    range(0, get_nargs(obj.__call__) - 1) ])))
        elif hasattr(obj, '__iter__'): # iterable (except str)
            return ComposerIterable(obj)
        else:
            raise NotImplementedError()


def iterable_composer(obj, *args, **kwargs):

    if args or kwargs:
        if callable(obj):
            return ComposerIterableFunction(obj, *args, **kwargs)
        else:
            raise NotImplementedError()
    else:
        if isinstance(obj, ComposerBase):
            return obj
        elif inspect.isgeneratorfunction(obj):
            return ComposerIterableFunction(obj, \
                    *(tuple([ ComposerArgs(idx) for idx in \
                    range(0, get_nargs(obj)) ])))
        elif inspect.isfunction(obj):
            return ComposerIterableFunction(obj, \
                    *(tuple([ ComposerArgs(idx) for idx in \
                    range(0, get_nargs(obj)) ])))
        elif inspect.ismethod(obj): # classmethod
            return ComposerIterableFunction(obj, \
                    *(tuple([ ComposerArgs(idx) for idx in \
                    range(0, get_nargs(obj) - 1) ])))
        elif callable(obj): # callbale but not function nor method
            return ComposerIterableFunction(obj, \
                    *(tuple([ ComposerArgs(idx) for idx in \
                    range(0, get_nargs(obj.__call__) - 1) ])))
        elif hasattr(obj, '__iter__'): # iterable (except str)
            return ComposerIterable(obj)
        else:
            raise NotImplementedError()


class ComposerBase(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def getArgSet(self):
        raise NotImplementedError()

    @abstractmethod
    def getKwargSet(self):
        raise NotImplementedError()
        
    @abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    @property
    def argset(self):
        return self.getArgSet()

    @property
    def kwargset(self):
        return self.getKwargSet()

class ComposerFunctionBase(ComposerBase):

    @abstractmethod
    def apply(self, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def run(self):
        raise NotImplementedError()

    @abstractmethod
    def bind(self, func):
        raise NotImplementedError()

    def __call__(self, *args, **kwargs):
        func = self.apply(*args, **kwargs)
        return func if len(func.getArgSet()) != 0 or \
                len(func.getKwargSet()) != 0 else func.run()

    def __rshift__(self, func):
        return self.bind(func)

class ComposerArgs(ComposerBase):

    def __init__(self, idx):
        self.idx = idx

    def __call__(self, *args, **kwargs):
        return args[self.idx] if self.idx < len(args) else \
                ComposerArgs(self.idx - len(args))

    def getArgSet(self):
        return (self.idx, )

    def getKwargSet(self):
        return ()


class ComposerKwargs(ComposerBase):

    def __init__(self, key):
        self.key = key

    def __call__(self, *args, **kwargs):
         return kwargs[self.key] if self.key in kwargs else self

    def getArgSet(self):
        return ()

    def getKwargSet(self):
        return (self.key,)


class ComposerFunction(ComposerFunctionBase):

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def getArgSet(self):
        return tuple(frozenset(reduce(operator.add, \
                [ arg.getArgSet() for arg in chain( \
                self.args, self.kwargs.values()) \
                if isinstance(arg, ComposerBase) ], ())))

    def getKwargSet(self):
        return tuple(frozenset(reduce(operator.add, \
                [arg.getKwargSet() for arg in chain( \
                self.args, self.kwargs.values()) \
                if isinstance(arg, ComposerBase)], ())))
        

    def apply(self, *args, **kwargs):

        def replaceArg(arg, *args, **kwargs):
            return arg(*args, **kwargs) if \
                    isinstance(arg, ComposerBase) else arg

        return self.__class__(self.func, \
            *(tuple([replaceArg(arg, *args, **kwargs) \
                for arg in self.args])), \
            **(dict([(key, replaceArg(value, *args, **kwargs)) \
                for key, value in self.kwargs.items() ])))

    def run(self):
        return self.func(*self.args, **self.kwargs)

    def bind(self, outf):
        return ComposerBind(self, outf)

class ComposerBuiltin(ComposerFunctionBase):

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def getArgSet(self): return ()

    def getKwargSet(self): return ()

    def apply(self, *args, **kwargs):
        self.kwargs.update(kwargs)
        return ComposerBuiltin(self.func,
                *(self.args + args), **(self.kwargs))

    def run(self):
        for nargs in range(0, len(self.args)+1):
            try:
                return self.func(*self.args[0:nargs], **self.kwargs)
            except TypeError:
                continue
        return self

    def bind(self, outf):
        return ComposerBind(self, outf)

class ComposerBind(ComposerFunctionBase):

    def __init__(self, inf, outf):
        self.inf = inf
        self.outf = outf

    def getArgSet(self):
        return self.inf.getArgSet()

    def getKwargSet(self):
        return tuple(frozenset(self.inf.getKwargSet() + \
                self.outf.getKwargSet()))


    def apply(self, *args, **kwargs):
        return ComposerBind(self.inf.apply(*args, **kwargs), \
            self.outf.apply(**kwargs))

    def run(self):
        return self.outf(*force_tuple(self.inf.run()))

    def bind(self, outf):
        return ComposerBind(self, outf)


class ComposerIterableBase(ComposerFunction):
    pass


class ComposerIterable(ComposerIterableBase):

    def __init__(self, it):
        self.it = it

    def getArgSet(self): return ()

    def getKwargSet(self): return ()

    def apply(self, *args, **kwargs): return self

    def run(self): return self.it

    def bind(self, func):
        return ComposerIterableBind(self, func)


class ComposerIterableFunction(ComposerIterableBase):

    def bind(self, func):
        return ComposerIterableBind(self, func)


class ComposerIterableBind(ComposerIterableBase):

    def __init__(self, it, func):
        self.it = it
        self.func = func

    def getArgSet(self):
        return self.it.getArgSet()

    def getKwargSet(self):
        return tuple(frozenset(self.it.getKwargSet() + \
                self.func.getKwargSet()))

    def apply(self, *args, **kwargs):
        return self.__class__( \
                self.it.apply(*args, **kwargs), \
                self.func.apply(**kwargs))

    def run(self):
        if isinstance(self.func, ComposerIterableBase):
            return self.func(*force_tuple(self.it()))
        else:
            return (self.func(*force_tuple(args)) for args in self.it())

    def bind(self, func):
        return self.__class__(self, func)


########################################################################
# main
########################################################################

if __name__ == '__main__':
    import unittest
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), 'test'))
    from composer_test import *

    unittest.main(verbosity=2)
