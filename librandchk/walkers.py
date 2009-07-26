class basic_walker(object):
    def __init__(self):
        self.files = []

    def add(self, file_list):
        self.files.extend(file_list)

    def __iter__(self):
        while self.files:
            yield self.files.pop()
