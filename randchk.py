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

from utils import obj, index_of_uniqe_element
from walkers import basic_walker

def debug(msg):
    if not options.debug:
        return

    if options.slave:
        msg = "%d: %s" %(os.getpid(), msg)
    sys.stderr.write("%s\n" %(msg, ))

class File(object):
    __slots__ = [ 'path', 'type' ]

    types = [ "REG", "DIR", "LNK", "BLK", "CHR", "FIFO", "SOCK" ]

    def __init__(self, type, path):
        if type not in File.types:
            raise Exception("Invalid type: %r" %(type))
        self.type = type
        self.path = path

    def __repr__(self):
        return "<File path=%r type=%r>" %(self.path, self.type)

def _check_file(file, slaves):
    # Compare 'file' across the slaves
    if file.type != "REG":
        # Ignore non-regular files... For now.
        return

    # TODO: Check file size

    for slave in slaves:
        slave.checksum(file.path)

    checksums = [ slave.last_checksum() for slave in slaves ]
    unique = index_of_uniqe_element(checksums)
    if unique is not None:
        # XXX: Need to include which slave this is...
        return ( file.path, "bad_checksum" )

    return None

def check_file(file, slaves):
    """ Check 'file' across 'slaves'.
        Returns a tuple '(file, description)' if any file causes an error. """
    from proxies import SlaveEnvError

    try:
        return _check_file(file, slaves)
    except SlaveEnvError, e:
        return ( e.filename, "env_error " + e.strerror )

def check(slaves, walker=basic_walker):
    """ Start checking that the files seen by 'slaves' are identical. """
    for file in walker(slaves[0].listdir):
        error = check_file(file, slaves)
        if error is not None:
            (problem_file, problem_description) = error
            yield ( problem_file, problem_description, file )

def run_master(args, help):
    if len(args) != 2:
        help()
        return 1

    from proxies import LocalSlaveProxy
    slaves = [ LocalSlaveProxy(dir) for dir in args ]

    for (canonical_file, problem_file, description) in check(slaves):
        print "%s: %s (%s)" %(problem_file, description, canonical_file)

    for slave in slaves:
        slave.shutdown()

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

def default_options():
    return obj((option, default) for
               (option, default, _, _, _) in ordered_options)

ordered_options = (
#   (name, default, short, long, help)
#    ("first1024", False, "-1", "--first-1024",
#        "Only check the first 1024 bytes of each file."),
#    ("show_progress", False, "-p", "--progress",
#        "Show a progress bar."),
    ("debug", True, "-d", "--debug",
        "Show debug information."),
    ("slave", False, "-s", "--slave",
        "(internal option)"),
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

    new_options = obj()

    # Load the options which have been changed into new_options
    for option, default_value in parser.defaults.items():
        new_value = getattr(parsed_options, option)
        if default_value != new_value:
            new_options[option] = new_value

    return (parser, args, new_options)

if __name__ == "__main__":
    sys.exit(run())
