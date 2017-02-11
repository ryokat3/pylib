<!-- ################################################################

Print out source code

import inspect
from test.singleton_test import *

print(inspect.getsource(eval("SingletonTest.test1")))

################################################################ -->

<!--#![PYTHON_EXEC]
import inspect
import os
import sys

sys.path.append(os.path.abspath('test'))

from singleton_test import *
-->

<!--#![PYTHON_EVAL] inspect.getsource(SingletonTest.test1) -->


# PyLib -- General Libray of Python Programming

- **Composer**: Currying and composing functions 

- **Singleton**: Simple Singleton and Parameterized Singleton

- **SelectExt**: A wrapper class for select 

- **IteratorExt**: Some extensions like itertools



## Motivation

A general programming tools, which is useful for any Python programs, like
itertools, functools etc.


## Examples

### Composer

1. Composing a function without 'def' statement

```python
# _0 is a place holder for positional argument
_0 = composer(0)

# Composing a function to calculate (x + 3) - 10
func = composer(operator.add, _0, 3) >> composer(operator.sub, _0, 10)

# Print '13' as a result
print(func(20))
```

2. Generating functions with parameters

```python

# _0 :       a place holder for 1st positional argument
# _add_val : a place holder for keyword argument 'add_val'
# _sub_val : a place holder for keyword argument 'sub_val'

_0 = composer(0)
_add_val = composer('add_val')
_sub_val = composer('sub_val')

# Composing a function to calculate (x + 3) - 10
func_tmpl = composer(operator.add, _0, _add_val) >> \
        composer(operator.sub, _0, _sub_val)
func = func_tmpl(add_val=3, sub_val=10)

# Print '13' as a result
print(func(20))
```


Installation
------------

Just copy a single file of what you need. 


License
-------

This software is released under the MIT License, see LICENSE.txt.
