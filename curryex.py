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

class ReaderEx(CurryEx):

    def __call__(self, *_args):
        def recv_state(_state):
            return super(ReaderEx, self).__call__(args=_args, state=_state)
        return recv_state

    @staticmethod
    def args(idx):
        def _(ary):
            return ary[idx]
        return CurryEx(_, CurryEx.Arg('args'))

    @staticmethod
    def state(key):
        def _(dic):
            return dic[key]
        return CurryEx(_, CurryEx.Arg('state'))


def readerex(*args, **kwargs):
    def decorator(func):
        return ReaderEx(func, *args, **kwargs)
    return decorator 



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

    def test_ReadeEx(self):
    
        _0 = ReaderEx.args(0)
        _1 = ReaderEx.args(1)
        _hehe = ReaderEx.state('hehe')
        _hoho = ReaderEx.state('hoho')

        add_ = ReaderEx(operator.add, _0, _hehe)
        sub_ = ReaderEx(operator.sub, _hoho, _0)

        func = unit(Reader, 1) >> add_ >> sub_

        self.assertEqual(func( { 'hehe': 2, 'hoho': 10 } ), 7)
        self.assertEqual(func( { 'hehe': 20, 'hoho': 100 } ), 79)


    def test_ReadeEx_decorator(self):

        _0 = ReaderEx.args(0)
        _1 = ReaderEx.args(1)
        _hehe = ReaderEx.state('hehe')
        _hoho = ReaderEx.state('hoho')

        @readerex(_0, _hehe)
        def add(a, b):
            return a + b

        @readerex(_hoho, _0)
        def sub(a, b):
            return a - b

        func = unit(Reader, 1) >> add >> sub

        self.assertEqual(func( { 'hehe': 2, 'hoho': 10 } ), 7)
        self.assertEqual(func( { 'hehe': 20, 'hoho': 100 } ), 79)

########################################################################
# main
########################################################################

if __name__ == '__main__':
    unittest.main()

