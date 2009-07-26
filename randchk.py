#!/usr/bin/env python
# Sorry, Python >= 2.5 only
from __future__ import division

import os
import sys

from utils import obj
from options import options, parse_options

def debug(msg):
    if not options.debug:
        return

    if options.slave:
        msg = "%d: %s" %(os.getpid(), msg)
    sys.stderr.write("%s\n" %(msg, ))

def run_master(args, help):
    if len(args) != 2:
        help()
        return 1

    from master import compare_directories
    for (problem_file, description, canonical_file) in compare_directories(args):
        print "%s: %s (%s)" %( problem_file, description, canonical_file )

    return 0

def run_slave(args, help):
    if len(args) != 1:
        sys.stderr.write("Slave got incorrect number of arguments.\n")
        sys.stderr.write("Expected 1, got %d.\n" %(len(args)))
        return 1

    from slave import Slave
    Slave(args[0]).run()
    return 0

def run():
    (parser, args, new_options) = parse_options()
    options.update(new_options)

    if options.slave:
        return run_slave(args, parser.print_help)
    else:
        return run_master(args, parser.print_help)

if __name__ == "__main__":
    sys.exit(run())
