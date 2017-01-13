#!/usr/bin/env python
#

import sys
import functools
import operator
from pymonad import *

if sys.version_info >= (3, 0):
    from functools import reduce

class Arg(object):

    def __init__(self, val):
        self.val = val

    def __eq__(self, other):
        if type(self) == type(other):
            return self.val == other.val
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.val)

    def __call__(self, *args, **kwargs):

        if isinstance(self.val, int):
            if self.val < len(args):
                return args[self.val]
            else:
                return Arg(self.val - len(args))
        else:
            if self in kwargs:
                return kwargs[self.val]
            elif self.val in kwargs:
                return kwargs[self.val]
            else:
                return self


def binder(func, *args, **kwargs):

    def is_replaced(arg):
        return not isinstance(arg, Arg)

    def replace(arg, *_args, **_kwargs):
        return arg if is_replaced(arg) else arg(*_args, **_kwargs)

    def _(*_args, **_kwargs):
        new_args = tuple([replace(arg, *_args, **_kwargs) for arg in args])
        new_kwargs = dict([(key, replace(value, *_args, **_kwargs)) \
            for key, value in kwargs.items() ])

        return func(*new_args, **new_kwargs) \
            if reduce(operator.__and__, \
                map(is_replaced, new_args), True) and \
                reduce(operator.__and__, \
                map(is_replaced, new_kwargs.values()), True) else \
            binder(func, *new_args, **new_kwargs)
    return _


class Curry(object):

    @staticmethod
    def _curry(func, nargs):
        def gen(g_nargs, *g_args):
            def _(*args):
                return gen(g_nargs - len(args), *(g_args + args))
            return _ if g_nargs > 0 else func(*g_args) 
        return gen(nargs)

    def __init__(self, func, nargs):
        self.func = self._curry(func, nargs)
        self.nargs = nargs

    def __call__(self, *args):
        return self.func(*args)

def identity(*args):            
    return args if len(args) > 1 else args[0]

def compose(f_outer, f_inner):
    def _tuplize(x):
        return x if isinstance(x, tuple) else (x,)

    def _(*args):
        return f_outer(*(_tuplize(f_inner(*args))))

    return _

def composable(func, *args, **kwargs):
    def _(_func):
        def recv_state(_state):
            return Curry(compose(binder(func, *args, **kwargs)(
                **_state), _func), _func.nargs)
        return recv_state
    return _



########################################################################
# main
########################################################################

if __name__ == '__main__':
    import unittest
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), 'test'))
    import composer_test

    unittest.main()

