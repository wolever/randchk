#!/usr/bin/env python
# Sorry, Python >= 2.5 only
from __future__ import with_statement

import os
from sys import exit
from optparse import OptionParser
from random import randint, random
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

def joinmany(dir, files):
    """ Join one directory to many files.
        >>> joinmany("/tmp/", ['a', 'b'])
        ['/tmp/a', '/tmp/b']
        >>> """
    return [ os.path.join(dir, file) for file in files ]

class random_file_walker(object):
    def __init__(self, dir):
        self.dir = dir
        # The number of files we've seen
        self.files = 0
        # The number of directories we've seen
        self.dirs = 0

    def __iter__(self):
        """ Recursively yield all the files in 'dir', randomly ordering them. """
        # XXX: Doesn't check for things like cyclic symlinks
        files = randlist(joinmany(self.dir, os.listdir(self.dir)))
        for file in files:
            if os.path.isdir(file):
                self.dirs += 1
                files.extend(joinmany(file, os.listdir(file)))
                continue
            self.files += 1
            yield file

def switchprefix(old, new, path):
    """ Switch the prefix of "path" from "old" to "new". """
    assert path.startswith(old)
    return new + path[len(old):]

def file_is_symlink(file):
    """ Symlinks, especially broken ones, cause lots of problems.
        Ignore them for now. """
    return S_ISLNK(os.stat(file).st_mode)

def file_size(file):
    """ Get a file's size. """
    return os.stat(file).st_size

def file_checksum(file):
    """ Checksum a file. """
    with open(file) as f:
        sum = md5()
        d = f.read(1024)
        while d:
            sum.update(d)
            d = f.read(1024)
        return sum.hexdigest()

def compare_files(*files):
    """ Compare a list of files, assuming that the first is considered
        "canonical" (that is, each file will be compared against the first).  A
        list of (file name, error description) tuples is reurned. """

    # A list of checks that will be performed.
    # If any check fails, no further checks are processed.
    # (this does have shortcomings, but it will do for now)
    for check in (file_size, file_checksum):
        problems = []

        # Check the "canonical" file.
        # Let any exceptions which happen here bubble up.
        canonical = check(files[0])

        # Check each individual file
        for file in files[1:]:
            problem = None
            try:
                result = check(file) 
                if canonical != result:
                    problem = "%s %s (expected) != %s (actual)" \
                               %(check.__name__, canonical, result)
            except EnvironmentError, e:
                problem = e.strerror

            if problem:
                problems.append((file, problem))
                problem = None

        if problems:
            return problems

    return []

def check_directories(dirs):
    """ Randomly walk over the "canonical" files in dirs[0], comparing them to
        the files in dirs[1:].  Triples of (canonical file path, problem file path,
        problem description) are yielded. """
    map(assert_dir, dirs)
    dirs = map(os.path.normpath, dirs)
    source_dir = dirs[0]
    dest_dirs = dirs[1:]
    walker = random_file_walker(source_dir)
    for source in walker:
        dests = [switchprefix(source_dir, dest_dir, source) for dest_dir in dest_dirs]
        problems = compare_files(source, *dests)
        for (problem_file, problem_description) in problems:
            yield source, problem_file, problem_description

if __name__ == '__main__':
    # Parse the command line arguments
    parser = OptionParser(usage = "usage: %prog [options] CANONICAL CHECK...\n"
        "\tRandomly checksum files in CANONICAL, comparing them to the same\n"
        "\tfile in each CHECK ensuring that they are the same.")
        
    #parser.add_option("-1", "--first-1024", action="store_true", dest="first1024",
    #                  help="Only check the first 1024 bytes of each file.")
    (options, args) = parser.parse_args()

    if len(args) != 2:
        parser.print_help()
        exit(1)

    for (canonical_file, problem_file, description) in check_directories(args):
        print "%s: %s (%s)" %(problem_file, description, canonical_file)
