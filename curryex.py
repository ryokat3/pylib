#!/usr/bin/env python
#

import unittest
import functools
import operator
from pymonad import *

class CurryEx(object):

    class Arg(object):
    
        def __init__(self, val):
            assert isinstance(val, int) or isinstance(val, str), \
                "val must be int or str"
            self.val = val
    
        def __eq__(self, other):
            if type(self) == type(other) and type(self.val) == type(other.val):
                return self.val == other.val
            else:
                return False

        def __ne__(self, other):
            return not self.__eq__(other)

        def __call__(self, *args, **kwargs):

            if isinstance(self.val, int):
                assert 0 <= self.val and self.val < len(args), \
                        "val(={}) is out of range".format(str(self.val))
                return args[self.val]
            elif isinstance(self.val, str):
                assert self.val in kwargs, \
                        "val(={}) is not key".format(str(self.val))
                return kwargs[self.val]
            else:
                raise TypeError(
                    "Type of val is {}".format(type(self.val)))

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        return self.func(
            *(self.replace_args(*args, **kwargs)), 
            **(self.replace_kwargs(*args, **kwargs)))

    def replace(self, arg, *args, **kwargs):
        return arg(*args, **kwargs) if \
            isinstance(arg, CurryEx) or isinstance(arg, CurryEx.Arg) \
            else arg 

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
# composer
########################################################################

def ComposerReader():
    def _(args, state):
        return args
    return unit(Reader, _)




def ComposerActivate(func, state={}):
    def _(*args):
        return func(state)(args)
    return _

def Composer(func, *args, **kwargs):

    this = CurryEx(func, *args, **kwargs)
    
    def combine(inner):
        def apply_state(_state):
            def tuplize(args):
                return args if isinstance(args, tuple) else (args, )
            def exec_curryex(args, state=_state):
                return this(args=tuplize(inner(args=tuplize(args),
                    state=state)), state=state)
            return exec_curryex
        return apply_state
    return combine


def Composer2(reader):
    def combine(inner):
        def apply_state(_state):
            def tuplize(args):
                return args if isinstance(args, tuple) else (args, )
            def exec_curryex(args, state=_state):
                return reader(state)(tuplize(inner(args=tuplize(args))))
            return exec_curryex
        return apply_state
    return combine



def argkey(key):
    assert isinstance(key, int) or isinstance(key, str), \
            "key must be int or str"

    def _(subscriptable):
        return subscriptable[key]

    return CurryEx(_, CurryEx.Arg('args')) if isinstance(key, int) else \
           CurryEx(_, CurryEx.Arg('state'))

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



class ComposerTest(unittest.TestCase):

    def test_composer(self):
    
        _0 = argkey(0)
        _1 = argkey(1)
        _hehe = argkey('hehe')
        _hoho = argkey('hoho')


        add_ = Composer(operator.add, _0, _hehe)
        sub_ = Composer(operator.sub, _hoho, _0)

        func = ComposerReader() >> add_ >> add_ >> sub_

        func1 = ComposerActivate(func, { 'hehe': 2, 'hoho': 10 } )

        self.assertEqual(func1(1), 5)
        self.assertEqual(func1(10), -4)

        func2 = ComposerActivate(func, { 'hehe': 3, 'hoho': 100 } )
        self.assertEqual(func2(10), 84)
        self.assertEqual(func2(20), 74)

        self.assertEqual(func1(1), 5)
        self.assertEqual(func1(10), -4)


    def test_composer_multiple_args(self):

        _0 = argkey(0)
        _1 = argkey(1)

        add_ = Composer(operator.add, _0, _1)

        func = ComposerReader() >> add_
        func1 = ComposerActivate(func)

        self.assertEqual(func1(3, 4), 7)
        self.assertEqual(func1(5, 6), 11)


        def addsub(c, d, a, b): return (a + b) * c, (a - b) * d

        _C = argkey('c')
        _D = argkey('d')

        addsub_ = Composer(addsub, _C, _D, _0, _1)
        func = ComposerReader() >> addsub_ 
        func1 = func >> Composer2(func) >> Composer2(func)

        func2 = ComposerActivate(func1, { 'c': 2, 'd': 3 }) 


        func3 = ComposerReader() >> addsub_  >> addsub_ >> addsub_
        func4 = ComposerActivate(func3, { 'c': 2, 'd': 3 }) 

        self.assertEqual(func2(20, 10), func4(20, 10))
        self.assertEqual(func2(20, 30), func4(20, 30))



########################################################################
# main
########################################################################

if __name__ == '__main__':
    unittest.main()

