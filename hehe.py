import inspect

class ClassSample(object):

  def __init__(self, val):
    'Hold a single value '
    self.val = val

print(inspect.getsource(ClassSample.__init__))
