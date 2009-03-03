#!/usr/bin/env python

import os
from os import path
from optparse import OptionParser

def assert_dir(f):
    """ Assert that 'f' is a directory. """
    assert path.isdir(f), "%r is not a directory!" %(f)

def randomly_walk_files(dir):
    """ Recursively yield all the files in 'dir', randomly ordering them. """
    files = randlist(os.listdir(dir))

def compare_directories(left, right):
    assert_dir(left)
    assert_dir(right)


# Parse the command line arguments
parser = OptionParser(usage = "usage: %prog [options] LEFT RIGHT\n"
    "\tRandomly checksum files in directories LEFT and RIGHT to ensure\n"
    "\tthat they are the same.")
    
parser.add_option("-1024", "--first-1024", action="store_true", dest="first1024",
                  help="Only check the first 1024 bytes of each file.")
(options, args) = parser.parse_args()
