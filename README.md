<!-- vim: set tabstop=4 expandtab shiftwidth=4 softtabstop=4: -->


PyLib -- General Libray for Python Programming
==============================================

- **Composer**: Currying and composing functions

- **Singleton**: Simple Singleton and Parameterized Singleton

- **SelectExt**: A wrapper class for select in socket programming

- **IteratorExt**: Some extensions like itertools



Motivation
----------

A useful programming tools for any Python programs.


Examples
--------

### Composing a parameterized function

```python
from composer import *

# _0 :       a place holder for 1st positional argument
# _add_val : a place holder for keyword argument 'add_val'
# _sub_val : a place holder for keyword argument 'sub_val'

_0 = composer(0)
_add_val = composer('add_val')
_sub_val = composer('sub_val')

# Composing a function to calculate (x + 3) - 10
func_comp = \
        composer(operator.add, _0, _add_val) >> \
        composer(operator.sub, _0, _sub_val)


# Generating a function :: (x + 3) - 10
func = func_comp(add_val=3, sub_val=10)
assert func(20) == 13

# Generating a function :: (x + 13) - 10
func = func_comp(add_val=13, sub_val=10)
assert func(20) == 23
```


### A parameterized singleton

`SingletonDict` provides a single instance for same parameters.

Python2

```python
class Test(object):
    __metaclass__ = SingletonDict
```

Python3

```python
class Test(object, metaclass=SingletonDict):
    pass
```

Python 2 & 3

```python
class Test(SingletonDict('Test', (object,), {})):
    pass
```

Usage

```python
from singleton import *

class Test(SingletonDict('Test', (object,), {})):

    def __init__(self, a, b):
        self.a = a
        self.b = b

test1 = Test(1, 2)
test2 = Test(b=2, a=1)

assert test1 == test2

test1.a = 3

assert test2.a == 3
```

Installation
------------

Just copy a single file of what you need.


License
-------

This software is released under the MIT License, see LICENSE.txt.
