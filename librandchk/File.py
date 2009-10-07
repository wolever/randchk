class File(object):
    """ Represents the relative path to a file.
        In other words, a File does not know which slave it is associated with.
        Or, a File represents a file which should be common to all slaves. """

    # We could have a lot of Files, so define which slots we'll be using.
    __slots__ = [ '_type', '_path', '_hashcode' ]

    types = [ "REG", "DIR", "LNK", "BLK", "CHR", "FIFO", "SOCK" ]

    def __init__(self, type, path):
        if type not in File.types:
            raise Exception("Invalid type: %r (path: %r)" %(type, path))
        self._hashcode = None
        self._type = type
        self._path = path

    @property
    def type(self):
        return self._type

    @property
    def path(self):
        return self._path

    def __hash__(self):
        if self._hashcode is None:
            self._hashcode = ( self.type, self.path ).__hash__()
        return self._hashcode

    def __eq__(self, other):
        if not isinstance(other, File):
            return False
        return other.type == self.type and other.path == self.path

    def __repr__(self):
        return "<File path=%r type=%r>" %(self.path, self.type)

