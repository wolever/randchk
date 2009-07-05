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

""" Currently un-unsed. """
#~ class file_walker(object):
#~     def __init__(self, dirname):
#~         self.dirname = dirname
#~         self.file_count = 0
#~         self.dir_count = 0
#~         self.files = None
#~ 
#~         if (options["show_progress"]):
#~             # The pretty progress bar.  The ETA is almost certainly a lie.
#~             p = pb.ProgressBar(widgets=['Checked: ', pb.Percentage(), ' ',
#~                                     pb.Bar(marker='=', left='[', right=']'),
#~                                     ' ', pb.ETA()],
#~                                 maxval=1)
#~             self.progress_bar = p
#~         else:
#~             self.progress_bar = None
#~ 
#~         self._init_()
#~ 
#~     def update_progress(self):
#~         if self.progress_bar is None:
#~             return
#~ 
#~         # Approximate the number of files left, given the average number of
#~         # files in each directory seen so far and the average file to directory
#~         # ratio.
#~         seen = self.dir_count + self.file_count
#~         # Remember, we have real division!
#~         # Also, the (... or 1) is to prevent the initial division by zero error.
#~         file_to_dir_ratio =  seen / (self.dir_count or 1)
#~         approx_left = file_to_dir_ratio * len(self.files)
#~         guess = seen + approx_left
#~         self.progress_bar.maxval = guess
#~         self.progress_bar.update(seen)
#~ 
#~     def __iter__(self):
#~         for file in self._iter_():
#~             self.update_progress()
#~             yield file
#~ 
#~     def _init_(self):
#~         raise Exception("_init_ needs to be implemented by subclasses.")
#~ 
#~     def _iter_(self):
#~         raise Exception("_iter_ needs to be implemented by subclasses.")
#~ 
#~ class random_file_walker(file_walker):
#~     def _init_(self):
#~         self.files = randlist(joinmany(self.dirname, os.listdir(self.dirname)))
#~ 
#~     def _iter_(self):
#~         """ Recursively yield all the files in 'dirname', randomly ordering
#~             them. """
#~         # XXX: Doesn't check for things like cyclic symlinks
#~         for file in self.files:
#~             if os.path.isdir(file):
#~                 self.dir_count += 1
#~                 self.files.extend(joinmany(file, os.listdir(file)))
#~                 continue
#~             self.file_count += 1
#~             yield file
