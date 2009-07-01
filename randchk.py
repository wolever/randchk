#!/usr/bin/env python
# Sorry, Python >= 2.5 only
from __future__ import with_statement
from __future__ import division

import os
import progressbar as pb
import sys
from optparse import OptionParser
from random import randint
from hashlib import md5

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

def joinmany(dirname, files):
    """ Join one directory to many files.
        >>> joinmany("/tmp/", ['a', 'b'])
        ['/tmp/a', '/tmp/b']
        >>> """
    return ( os.path.join(dirname, file) for file in files )

class file_walker(object):
    def __init__(self, dirname):
        self.dirname = dirname
        self.file_count = 0
        self.dir_count = 0
        self.files = None

        if (options["show_progress"]):
            # The pretty progress bar.  The ETA is almost certainly a lie.
            p = pb.ProgressBar(widgets=['Checked: ', pb.Percentage(), ' ',
                                    pb.Bar(marker='=', left='[', right=']'),
                                    ' ', pb.ETA()],
                                maxval=1)
            self.progress_bar = p
        else:
            self.progress_bar = None

        self._init_()

    def update_progress(self):
        if self.progress_bar is None:
            return

        # Approximate the number of files left, given the average number of
        # files in each directory seen so far and the average file to directory
        # ratio.
        seen = self.dir_count + self.file_count
        # Remember, we have real division!
        # Also, the (... or 1) is to prevent the initial division by zero error.
        file_to_dir_ratio =  seen / (self.dir_count or 1)
        approx_left = file_to_dir_ratio * len(self.files)
        guess = seen + approx_left
        self.progress_bar.maxval = guess
        self.progress_bar.update(seen)

    def __iter__(self):
        for file in self._iter_():
            self.update_progress()
            yield file

    def _init_(self):
        raise Exception("_init_ needs to be implemented by subclasses.")

    def _iter_(self):
        raise Exception("_iter_ needs to be implemented by subclasses.")

class random_file_walker(file_walker):
    def _init_(self):
        self.files = randlist(joinmany(self.dirname, os.listdir(self.dirname)))

    def _iter_(self):
        """ Recursively yield all the files in 'dirname', randomly ordering
            them. """
        # XXX: Doesn't check for things like cyclic symlinks
        for file in self.files:
            if os.path.isdir(file):
                self.dir_count += 1
                self.files.extend(joinmany(file, os.listdir(file)))
                continue
            self.file_count += 1
            yield file

def switchprefix(old, new, path):
    """ Switch the prefix of "path" from "old" to "new". """
    assert path.startswith(old)
    return new + path[len(old):]

def file_is_symlink(file):
    """ Symlinks, especially broken ones, cause lots of problems.
        Ignore them for now. """
    return os.path.islink(file)

def file_size(file):
    """ Get a file's size. """
    return os.stat(file).st_size

def file_summer(file):
    with open(file) as f:
        sum = md5()
        data = f.read(1024)
        while data:
            sum.update(data)
            yield sum.hexdigest()
            data = f.read(1024)

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

def _compare_files(*files):
    if file_is_symlink(files[0]):
        return None

    expected_size = file_size(files[0])
    for file in files[1:]:
        size = file_size(file)
        if size != expected_size:
            return (file, "file_size %s != %s" %(size, expected_size))

    # Checksum the files
    error = None
    sums = [ file_summer(f) for f in files ]
    while error is None:
        try:
            these_sums = [ sum.next() for sum in sums ]
        except StopIteration, e:
            break

        unique = index_of_uniqe_element(these_sums)
        if unique is not None:
            error = (files[unique], "bad_checksum")

        if options["first1024"]:
            break

    return error

def compare_files(*files):
    """ Compare a list of files, assuming that the first is considered
        "canonical" (that is, each file will be compared against the first).
        A (file name, error description) tuple or None is reurned. """

    try:
        return _compare_files(*files)
    except EnvironmentError, e:
        return (e.filename, "env_error %s" %(e.strerror))

def check_directories(dirs):
    """ Randomly walk over the "canonical" files in dirs[0], comparing them to
        the files in dirs[1:].  Triples of (canonical file path, problem file path,
        problem description) are yielded. """
    # Make sure that everything we've been passed is, in fact, a directory
    map(assert_dir, dirs)

    dirs = map(os.path.normpath, dirs)
    source_dir = dirs[0]
    dest_dirs = dirs[1:]

    walker = random_file_walker(source_dir)
    for source in walker:
        dests = ( switchprefix(source_dir, dest_dir, source)
                  for dest_dir in dest_dirs )
        error = compare_files(source, *dests)
        if error is not None:
            (problem_file, problem_description) = error
            yield source, problem_file, problem_description

def default_options():
    return dict((option, default) for
                (option, default, _, _, _) in ordered_options)

ordered_options = (
#   (name, default, short, long, help)
    ("first1024", False, "-1", "--first-1024",
        "Only check the first 1024 bytes of each file."),
    ("show_progress", False, "-p", "--progress",
        "Show a progress bar."),
)

options = default_options()

def parse_options():
    # Parse the command line arguments
    parser = OptionParser(usage = "usage: %prog [options] CANONICAL CHECK...\n"
        "\tRandomly checksum files in CANONICAL, comparing them to the same\n"
        "\tfile in each CHECK ensuring that they are the same.")

    for (name, _, short, long, help) in ordered_options:
        parser.add_option(short, long, action="store_true",
                          dest=name, help=help)
        
    (parsed_options, args) = parser.parse_args()

    new_options = {}

    # Load the options which have been changed into new_options
    for option, default_value in parser.defaults.items():
        new_value = getattr(parsed_options, option)
        if default_value != new_value:
            new_options[option] = new_value

    return (parser, args, new_options)

if __name__ == "__main__":
    (parser, args, new_options) = parse_options()
    options.update(new_options)

    if len(args) != 2:
        parser.print_help()
        sys.exit(1)

    for (canonical_file, problem_file, description) in check_directories(args):
        print "%s: %s (%s)" %(problem_file, description, canonical_file)
