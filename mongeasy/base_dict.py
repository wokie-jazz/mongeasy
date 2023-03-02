"""
Base class for the Document class
Implements the dict methods
"""
from copy import deepcopy


class BaseDict(dict):
    """
    This class is used as a base class for the Document class
    Implements the dict methods
    """
    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def __getitem__(self, key):
        return self.__dict__[key]

    def __repr__(self):
        return repr(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __delitem__(self, key):
        del self.__dict__[key]

    def clear(self):
        return self.__dict__.clear()

    def copy(self):
        # get the class of the current object
        cls = self.__class__
        return cls(self.__dict__.copy())

    def deepcopy(self):
        # get the class of the current object
        cls = self.__class__
        return cls(deepcopy(self.__dict__))

    def has_key(self, k):
        return k in self.__dict__

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def pop(self, *args):
        return self.__dict__.pop(*args)

    def popitem(self):
        return self.__dict__.popitem()
    
    def setdefault(self, *args):
        return self.__dict__.setdefault(*args)
    
    def __cmp__(self, dict_):
        return super().__cmp__(self.__dict__, dict_)

    def __contains__(self, item):
        return item in self.__dict__