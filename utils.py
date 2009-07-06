import re
import shlex

from random import randint
from types import GeneratorType
from os import path

class obj(dict):
    def __getattr__(self, key):
        return self[key]

class randlist(list):
    def __iter__(self):
        """ Return random items while being iterated over.
            Note that it is ok to add items between yields. """
        while len(self):
            topop = randint(0, len(self) - 1)
            yield self.pop(topop)

def assert_dir(f):
    """ Assert that 'f' is a directory. """
    assert path.isdir(f), "%r is not a directory!" %(f)

def index_of_uniqe_element(elements):
    """ If 'i' contains an element which is not the same as the rest, return
        its index or None.
        index_of_uniqe_element([]) is undefined.
        >>> index_of_uniqe_element(["a"])
        None
        >>> index_of_uniqe_element(["a", "a"])
        None
        >>> index_of_uniqe_element(["a", "x"])
        1
        >>> """
    first_element = None
    for (id, element) in enumerate(elements):
        if first_element is None:
            first_element = element

        if element != first_element:
            return id
    return None

def shellquote(s):
    s = s.replace('"', r'\"') # Escape any single-quotes
    if re.search(r"\s", s):
        # Only quote the string if it contains whitespace
        s = '"' + s + '"'
    return s

def shellunquote(s):
    return shlex.split(s)

class SerializationError(Exception):
    pass

def unserialize(s):
    lines = s.split("\n")
    if len(lines) > 1:
        return [ tuple(shellunquote(line)) for line in lines ]
    else:
        return tuple(shellunquote(lines[0]))

def serialize(obj, recurse=None):
    # Serialize a tuple which contains strings, or a list
    # which contains tuples.
    if isinstance(obj, GeneratorType) and recurse == None:
        return serialize(list(obj))

    elif isinstance(obj, list) and recurse == None:
        return "\n".join(serialize(item, "list") for item in obj)

    elif isinstance(obj, tuple) and recurse in (None, "list"):
        return " ".join(serialize(item, "tuple") for item in obj)

    if isinstance(obj, basestring) and recurse == "tuple":
        return shellquote(obj)

    else:
        raise SerializationError("Can't serialize %r" %(obj))
