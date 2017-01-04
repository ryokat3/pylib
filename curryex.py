#!/usr/bin/env python
#

import unittest
import functools
import operator
from pymonad import *

class CurryEx(object):

    class Exception(Exception):
        pass

    class Arg(object):
    
        def __init__(self, val):
            self.val = val
    
        def __eq__(self, other):
            if type(self) == type(other) and type(self.val) == type(other.val):
                return self.val == other.val
            else:
                return False

        def __ne__(self, other):
            return not self.__eq__(other)

        def get_arg(self, *args, **kwargs):
            if isinstance(self.val, int):
                return args[self.val]
            elif isinstance(self.val, str):
                return kwargs[self.val]
            else:
                raise CurryEx.Exception()

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        return self.func(
            *(self.replace_args(*args, **kwargs)), 
            **(self.replace_kwargs(*args, **kwargs)))

    def replace(self, arg, *args, **kwargs):
        return arg.get_arg(*args, **kwargs) if isinstance(arg, CurryEx.Arg) else \
            arg(*args, **kwargs) if isinstance(arg, CurryEx) else arg 

    def replace_args(self, *args, **kwargs):
        return [ self.replace(arg, *args, **kwargs) for arg in self.args ]

    def replace_kwargs(self, *args, **kwargs):
        return dict([ (key, self.replace(value, *args, **kwargs)) \
            for key, value in self.kwargs ])


def curryex(*args, **kwargs):
    def decorator(func):
        return CurryEx(func, *args, **kwargs)
    return decorator
            
########################################################################
# reader
########################################################################

def readerex(func, *args, **kwargs):
    def recv_args(*_args):
        def recv_state(_state):
            return CurryEx(func, *args, **kwargs)(args=_args, state=_state)
        return recv_state
    return recv_args 

def args_(idx):
    def _(args):
        return args[idx]
    return CurryEx(_, CurryEx.Arg('args'))

def state_(key):
    def _(state):
        return state[key]
    return CurryEx(_, CurryEx.Arg('state'))



########################################################################
# unittest
########################################################################

class CurryExTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self._0 = CurryEx.Arg(0)
        self._1 = CurryEx.Arg(1)
        self._2 = CurryEx.Arg(2)
        self._hehe = CurryEx.Arg('hehe')

    def tearDown(self):
        pass

    def test_Arg(self):
        self.assertEqual(CurryEx.Arg(1), CurryEx.Arg(1))
        self.assertNotEqual(CurryEx.Arg(1), CurryEx.Arg(2))
        self.assertNotEqual(CurryEx.Arg(1), CurryEx.Arg('1'))

    def test_CurryEx(self):

        func1 = CurryEx(operator.add, self._0, 2)
        self.assertEqual(func1(1), 3)

        func2 = CurryEx(operator.sub, self._1, self._0)
        self.assertEqual(func2(2, 3), 1)

        func3 = CurryEx(operator.add, 10, self._hehe)
        self.assertEqual(func3(hehe=1), 11)

        func4 = CurryEx(operator.sub,
            CurryEx(operator.add, self._2, self._1), self._0)
        self.assertEqual(func4(1, 2, 3), 4)

    def test_CurryEx_decorator(self):

        @curryex(self._1, self._0)
        def sub(a, b):
            return a - b

        self.assertEqual(sub(1, 2), 1)
        self.assertEqual(sub(10, 20), 10)

        @curryex(sub, self._2)
        def sub2(a, b):
            return a - b

        self.assertEqual(sub2(10, 20, 5), 5)
        self.assertEqual(sub2(10, 30, 5), 15)



class ReaderExTest(unittest.TestCase):

    def test_reader(self):
    
        _0 = args_(0)
        _1 = args_(1)
        _hehe = state_('hehe')
        _hoho = state_('hoho')

        add_ = readerex(operator.add, _0, _hehe)
        sub_ = readerex(operator.sub, _hoho, _0)

        func = unit(Reader, 1) >> add_ >> sub_

        self.assertEqual(func( { 'hehe': 2, 'hoho': 10 } ), 7)

########################################################################
# main
########################################################################

if __name__ == '__main__':
    unittest.main()

