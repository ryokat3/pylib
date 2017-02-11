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


func = func_comp(add_val=3, sub_val=10)

# Print '13' as a result
print(func(20))

func = func_comp(add_val=13, sub_val=10)
# Print '23' as a result
print(func(20))
