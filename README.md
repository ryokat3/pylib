<!-- ----------------------------------------------------------------
----------------------------------------------------------------- -->
## Synopsis

**pylib** is a small library of python tool.

- **Composer** : Currying and composing functions 


## Code Example

### Composer

```python
# Composing a function to calculate (x + 3) - 10

_0 = composer(0)
func = composer(operator.add, 3) >> composer(operator.sub, _0, 10)
```

```python
# _0 :          a place holder for positional argument
# _add_val : a place holder for keyword argument 'add_val'
# _sub_val : a place holder for keyword argument 'sub_val'
_0 = composer(0)
_add_val = composer('add_val')
_sub_val = composer('sub_val')

# Composing a function to calculate (x + 3) - 10
func_temp = composer(operator.add, _0, _add_val) >> \
        composer(operator.sub, _0, _sub_val)
func = func_tmp(add_val=3, sub_val=10)

# Print '17' as a result
print(func(20))
```

## Motivation

A general programming tools, which is useful for any Python programs, like
itertools, functools etc.


## Installation

Installation is to clone GIT repository of this project


<!--
## API Reference

Depending on the size of the project, if it is small and simple enough the reference docs can be added to the README. For medium size to larger projects it is important to at least provide a link to where the API reference docs live.

## Tests

Describe and show how to run the tests with code examples.

## Contributors

Let people know how they can dive into the project, include important links to things like issue trackers, irc, twitter accounts if applicable.
-->

## License

This software is released under the MIT License, see LICENSE.txt.
