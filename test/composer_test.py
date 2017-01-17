#!/usr/bin/env python
#

import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from composer import *

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

    def test_composal_unmatch(self):
        _0 = Arg(0)
        _1 = Arg(1)
        _VAL = Arg('VAL')

        starter = Curry(identity, 3)
        def calc(a, b, c):
            return (a - b) * c, (b - a) * c

        def calc2(a, b, c):
            return (a - b) * c, (b - a) * c, 'hehe'

        calc_ = composable(calc, _0, _1, _VAL)
        monad = unit(Reader, starter) >> calc_ 
        func = monad({'VAL':10})
        self.assertEqual(func(7, 5, 100), (20, -20))

        calc2_ = composable(calc2, _0, _1, _VAL)
        monad = unit(Reader, starter) >> calc2_ >> calc_ 
        func = monad({'VAL':10})
        self.assertEqual(func(7, 5, 'hello'), (400, -400))


    def test_composal_partial_state(self):
        _0 = Arg(0)
        _1 = Arg(1)
        _VAL1 = Arg('VAL1')
        _VAL2 = Arg('VAL2')

        starter = Curry(identity, 1)
        def calc(a, b, c):
            return (a - b) * c, (b - a) * c

        calc_ = composable(calc, _VAL1, _0, _VAL2)
        monad = unit(Reader, starter) >> calc_ 
        func = monad({'VAL1':10})
        func2 = func({'VAL2':20})
        self.assertEqual(func2(5), (100, -100))

########################################################################
# main
########################################################################

if __name__ == '__main__':
    unittest.main(verbosity=2)
