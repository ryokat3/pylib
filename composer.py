#!/usr/bin/env python
#

import sys
import unittest
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


class ArgTest(unittest.TestCase):

    def test_equality(self):
        self.assertEqual(Arg(1), Arg(1))
        self.assertNotEqual(Arg(1), Arg(2))
        self.assertNotEqual(Arg(1), Arg('1'))
    

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

class CurryexTest(unittest.TestCase):

    def test_replace_positional_args(self):
        _0 = Arg(0)
        _1 = Arg(1)

        func = binder(operator.sub, _1, _0)
        self.assertEqual(func(1, 2), 1)
        self.assertEqual(func(3)(10), 7)

    def test_replace_keyword_args(self):
        _0 = Arg(0)
        _1 = Arg(1)

        def sub(a, b):
            return a - b
        func = binder(sub, b=_0, a=_1)
        self.assertEqual(func(1, 2), 1)
        self.assertEqual(func(3)(10), 7)


    def test_keyword_args(self):
        _a1 = Arg('a1')
        _a2 = Arg('a2')

        def sub(a, b):
            return a - b
        func = binder(sub, b=_a1, a=_a2)
        self.assertEqual(func(a1=1, a2=2), 1)
        self.assertEqual(func(a1=3)(a2=10), 7)


    def test_mixed_args(self):
        _0 = Arg(0)
        _a1 = Arg('a1')

        def sub(a, b):
            return a - b
        func = binder(sub, b=_a1, a=_0)
        self.assertEqual(func(2, a1=1), 1)
        self.assertEqual(func(a1=3)(10), 7)

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


class ComposeTest(unittest.TestCase):

    def test_Curry(self):

        func = Curry(identity, 4)
        self.assertEqual(func.nargs, 4)
        self.assertEqual(func(1, 2, 3, 4), (1, 2, 3, 4))
        self.assertEqual(func(1)(2, 3, 4), (1, 2, 3, 4))
        self.assertEqual(func(1)(2)(3)(4), (1, 2, 3, 4))
        self.assertEqual(func(1)(2)(3, 4), (1, 2, 3, 4))

    def test_starter_reader(self):
        starter = Curry(identity, 1)
        func = unit(Reader, starter)(None)
        self.assertEqual(func('hello'), 'hello')
        self.assertEqual(func(123), 123)

    def test_starter_reader_multi(self):
        starter = Curry(identity, 3)
        func = unit(Reader, starter)(None)
        self.assertEqual(func('hello', 1, 2), ('hello', 1, 2))
        self.assertEqual(func('hello')(1, 2), ('hello', 1, 2))
        self.assertEqual(func('hello', 1)(2), ('hello', 1, 2))
        self.assertEqual(func('hello')(1)(2), ('hello', 1, 2))

    def test_composal(self):
        _0 = Arg(0)
        _VAL = Arg('VAL')

        starter = Curry(identity, 1)
        add = composable(operator.add, _0, _VAL)
        monad = unit(Reader, starter) >> add
        func = monad({'VAL':10})
        self.assertEqual(func(3), 13)
        self.assertEqual(func(7), 17)

    def test_composal_multi(self):
        _0 = Arg(0)
        _1 = Arg(1)
        _VAL = Arg('VAL')

        starter = Curry(identity, 2)
        def calc(a, b, c):
            return (a - b) * c, (b - a) * c

        calc_ = composable(calc, _0, _1, _VAL)
        monad = unit(Reader, starter) >> calc_ 
        func = monad({'VAL':10})
        self.assertEqual(func(7, 5), (20, -20))

        calc_ = composable(calc, _1, _0, _VAL)
        monad = unit(Reader, starter) >> calc_ 
        func = monad({'VAL':10})
        self.assertEqual(func(7, 5), (-20, 20))

        monad = unit(Reader, starter) >> calc_ >> calc_
        func = monad({'VAL':10})
        self.assertEqual(func(7, 5), (400, -400))


########################################################################
# main
########################################################################

if __name__ == '__main__':
    unittest.main()

