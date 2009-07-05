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
    assert os.path.isdir(f), "%r is not a directory!" %(f)

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

