class basic_walker(object):
    def __init__(self, list, root="/"):
        # 'list' is a function which accepts a path and return a list of files.
        # currently it is assumed that this list will be in the form:
        #    [ ( type, path ), ... ]
        # where 'path' is the complete path:
        #    >>> x = list("/tmp/")[0]
        #    >>> x.path
        #    '/tmp/x.py'
        #    >>> x.type
        #    'REG'
        #    >>>
        self.list = list
        self.root = "/"

    def __iter__(self):
        files = list(self.list(self.root))
        while files:
            file = files.pop()
            if file.type == "DIR":
                files.extend(self.list(file.path))
                continue
            yield file
