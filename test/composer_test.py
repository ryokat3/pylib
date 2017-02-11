#!/usr/bin/env python
#

import operator
import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from composer import *



class ComposerValueTest(unittest.TestCase):

    def test(self):
        arg = ComposerValue(1)
        self.assertEqual(arg(), 1)

        arg = ComposerValue(operator.add)
        self.assertEqual(arg(), operator.add)

        func = composer(operator.add)
        arg = ComposerValue(func)
        self.assertEqual(arg(), func)


class ComposerArgsTest(unittest.TestCase):

    def test(self):
        _0 = composer(0)
        _1 = composer(1)
        _2 = composer(2)
        _3 = composer(3)

        self.assertEqual(_0.argset, (0,))
        self.assertEqual(_1.argset, (1,))

        self.assertFalse(_0.kwargset)

        self.assertEqual(_0(0,1,2), 0)
        self.assertEqual(_1(0,1,2), 1)

        self.assertEqual(_3(0,1,2)(0,1,2), 0)
        self.assertEqual(_3(0)(0)(0)(1), 1)


class ComposerKwArgsTest(unittest.TestCase):

    def test(self):
        _a1 = composer('a1')
        _a2 = composer('a2')
        _a3 = composer('a3')
        _a4 = composer('a4')

        self.assertEqual(_a1.kwargset, ('a1',))
        self.assertEqual(_a2.kwargset, ('a2',))

        self.assertFalse(_a1.argset)

        self.assertEqual(_a1(0,1,a1=1), 1)
        self.assertEqual(_a2(0,1,a2=2,a1=1), 2)



class ComposerFunctionTest(unittest.TestCase):

    def test_Args(self):
        _0 = composer(0)
        _1 = composer(1)
        sub = composer(operator.sub, _1, _0)

        self.assertEqual(sub(1, 10), 9)
        self.assertEqual(sub(1)(10), 9)

    def test_Kwargs(self):
        _a1 = composer('a1')
        _a2 = composer('a2')
        sub = composer(operator.sub, _a1, _a2)

        self.assertEqual(sub(a1=10, a2=1), 9)
        self.assertEqual(sub(a2=1)(a1=10), 9)

    def test_MixedArgs(self):
        _1 = composer(1)
        _a1 = composer('a1')
        sub = composer(operator.sub, _a1, _1)

        self.assertEqual(sub(1000, 1, a1=10), 9)
        self.assertEqual(sub(1000)(1)(a1=10), 9)
        self.assertEqual(sub(a1=10)(1000, 1), 9)

    def test_invert(self):

        comp = composer(lambda x: x+1)
        self.assertEqual(comp(3), 4)
        self.assertTrue(callable(comp))
        add = composer(operator.add, comp, 2)
        self.assertEqual(add(1), 4)

        def do(func, arg):
            return func(arg) if callable(func) else (func, arg)
        self.assertEqual(composer(do)(lambda x: x+1)(3), 4)
        self.assertEqual(composer(do)(comp)(3), (4, 3))

        self.assertEqual(composer(do)(~comp)(3), 4)


class ComposerBuiltinTest(unittest.TestCase):

    def test_solo(self):
        add = composer(operator.add)
        self.assertEqual(add(1,2), 3)
        self.assertEqual(add(1)(2), 3)
        self.assertEqual(add(1)(2,3), 3)

    def test_combo(self):
        add = composer(operator.add)
        sub = composer(operator.sub)
        func = add(1) >> sub(100)
        self.assertEqual(func(1), 98)
        self.assertEqual(func(10), 89)
        func = add(100) >> sub(200)
        self.assertEqual(func(12), 88)

    def test_combo2(self):
        _0 = composer(0)
        _1 = composer(1)
        add = composer(operator.add)
        sub = composer(operator.sub, _0, _1)
        func = add(1) >> sub(100)
        self.assertEqual(func(1), 98)
        self.assertEqual(func(10), 89)
        func = add(100) >> sub(200)
        self.assertEqual(func(12), 88)

    def test_1(self):
        def ret10():
            return 10
        func = composer(ret10)
        self.assertNotEqual(func, 10)
        self.assertEqual(func(), 10)

    def test_2(self):
        def ret10():
            return 10
        func = composer(ret10) >> composer(operator.add)(10)
        self.assertNotEqual(func, 20)
        self.assertEqual(func(), 20)


class ComposerFunctionBind(unittest.TestCase):

    def test_bind_1(self):

        _0 = composer(0)
        add10 = composer(operator.add, 10, _0)

        func = add10 >> add10
        self.assertEqual(func.argset, (0,))
        self.assertEqual(func(1), 21)
        self.assertEqual(func(2), 22)


    def test_bind_2(self):

        _0 = composer(0)
        add10 = composer(operator.add, 10, _0)

        func = add10(add10)

        self.assertEqual(func.argset, (0,))
        self.assertEqual(func(1), 21)
        self.assertEqual(func(2), 22)

        func = add10 >> add10 >> add10

        self.assertEqual(func.argset, (0,))
        self.assertEqual(func(1), 31)
        self.assertEqual(func(2), 32)

        func = func >> add10 >> func

        self.assertEqual(func.argset, (0,))
        self.assertEqual(func(1), 71)
        self.assertEqual(func(2), 72)

    def test_bind_multiple_values(self):
        _0 = composer(0)
        _1 = composer(1)
        def calc(a, b):
            return a + b, a - b
        func = composer(calc, _0, _1)

        func = func >> func >> func

        self.assertEqual(func(20, 10), (60, 20))
        self.assertEqual(func(20)(10), (60, 20))

    def test_wrap_function(self):

        def calc(a, b):
            return a + b, a - b
        func = composer(calc)
        self.assertEqual(func.argset, (0,1))

        func = func >> func >> func

        self.assertEqual(func(20, 10), (60, 20))
        self.assertEqual(func(20)(10), (60, 20))

    def test_wrap_callable(self):

        class calc(object):
            def __call__(self, a, b):
                return a + b, a - b
        func = composer(calc())
        self.assertEqual(func.argset, (0,1))

        func = func >> func >> func

        self.assertEqual(func(20, 10), (60, 20))
        self.assertEqual(func(20)(10), (60, 20))

    def test_wrap_classmethod(self):

        class calc(object):
            @classmethod
            def call(cls, a, b):
                return a + b, a - b
        func = composer(calc.call)
        self.assertEqual(func.argset, (0,1))

        func = func >> func >> func

        self.assertEqual(func(20, 10), (60, 20))
        self.assertEqual(func(20)(10), (60, 20))

    def test_wrap_staticmethod(self):

        class calc(object):
            @staticmethod
            def call(a, b):
                return a + b, a - b
        func = composer(calc.call)
        self.assertEqual(func.argset, (0,1))

        func = func >> func >> func

        self.assertEqual(func(20, 10), (60, 20))
        self.assertEqual(func(20)(10), (60, 20))


class ComposerOr(unittest.TestCase):

    def test_1(self):
        func = composer(operator.add) | composer(operator.sub)
        self.assertEqual(func(10, 5), (15, 5))

    def test_2(self):
        func = composer(operator.add) | composer(operator.sub) \
                >> composer(operator.add)(10)
        self.assertEqual(func(10, 5), (15, 15))

    def test_3(self):
        func = (composer(operator.add) | composer(operator.sub)) \
                >> composer(operator.add)
        self.assertEqual(func(10, 5), 20)

    def test_4(self):
        func = (composer(operator.add) | composer(operator.sub)) >> \
                (composer(operator.add) | composer(operator.sub)) \
                >> composer(operator.add)
        self.assertEqual(func(10, 5), 30)

    def test_5(self):
        func = (composer(operator.add) | composer(operator.sub)) >> \
                (composer(operator.add) | 20) \
                >> composer(operator.add)
        self.assertEqual(func(10, 5), 40)


class ComposerIterableTest(unittest.TestCase):

    def test_iterable(self):
        gen = composer(range(3))

        self.assertEqual(tuple([ a for a in gen() ]), (0, 1, 2))


class ComposerIterableBindTest(unittest.TestCase):

    def test_iterable_bind(self):
        _0 = composer(0)
        gen = composer(range(3))
        add10 = composer(operator.add, 10, _0)

        iterable = gen >> add10
        self.assertEqual(tuple([ a for a in iterable() ]), (10, 11, 12))


class ComposerIterableFunctionTest(unittest.TestCase):

    def test_iterable(self):
        _0 = composer(0)
        _1 = composer(1)

        def gensub(a, b):
            for i in range(0, a - b):
                yield i
        add10 = composer(operator.add, 10, _0)

        gen = composer(gensub) >> add10
        self.assertEqual(tuple([ a for a in gen(10, 7) ]), (10, 11, 12))
        self.assertEqual(tuple([ a for a in gen(10)(7) ]), (10, 11, 12))

        gen = composer(gensub, _1, _0) >> add10
        self.assertEqual(tuple([ a for a in gen(7, 10) ]), (10, 11, 12))
        self.assertEqual(tuple([ a for a in gen(7)(10) ]), (10, 11, 12))


    def test_iterable_composer_iter_func(self):
        _0 = composer(0)
        _1 = composer(1)

        def gensub(a, b):
            return range(0, a - b)
        add10 = composer(operator.add, 10, _0)

        gen = iterable_composer(gensub) >> add10
        self.assertEqual(tuple([ a for a in gen(10, 7) ]), (10, 11, 12))
        self.assertEqual(tuple([ a for a in gen(10)(7) ]), (10, 11, 12))

        gen = iterable_composer(gensub, _1, _0) >> add10
        self.assertEqual(tuple([ a for a in gen(7, 10) ]), (10, 11, 12))
        self.assertEqual(tuple([ a for a in gen(7)(10) ]), (10, 11, 12))


    def test_iterable_composer_iter_iter(self):
        _0 = composer(0)
        _1 = composer(1)

        def gen(a):
            for i in range(0, a):
                yield i

        def mod(it, x):
            for i in it:
                if (i % x) == 0:
                    yield i

        func = composer(gen) >> composer(mod, _0, 2)
        self.assertEqual(tuple(list(func(10))), (0,2,4,6,8))


    def test_iterable_composer_iter_func_iter(self):
        _0 = composer(0)
        _1 = composer(1)

        def gen(a):
            for i in range(0, a):
                yield i

        def mod(it, x):
            for i in it:
                if (i % x) == 0:
                    yield i

        add10 = composer(operator.add, 10, _0)

        func = composer(gen) >> add10 >> composer(mod, _0, 2)
        self.assertEqual(tuple(list(func(10))), (10,12,14,16,18))


########################################################################
# main
########################################################################

if __name__ == '__main__':

    unittest.main(verbosity=2)
