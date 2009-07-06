#!/usr/bin/env python
# Sorry, Python >= 2.5 only
from __future__ import with_statement
from __future__ import division

import os
import sys

from optparse import OptionParser

from utils import obj, index_of_uniqe_element
from walkers import basic_walker

def debug(msg):
    if not options.debug:
        return

    if options.slave:
        msg = "%d: %s" %(os.getpid(), msg)
    sys.stderr.write("%s\n" %(msg, ))

class File(object):
    """ Represents the relative path to a file.
        In other words, a File does not know which slave it is associated with.
        Or, a File represents a file which should be common to all slaves. """

    # We could have a lot of Files, so define which slots we'll be using.
    __slots__ = [ 'type', 'path' ]

    types = [ "REG", "DIR", "LNK", "BLK", "CHR", "FIFO", "SOCK" ]

    def __init__(self, type, path):
        if type not in File.types:
            raise Exception("Invalid type: %r" %(type))
        self.type = type
        self.path = path

    def __repr__(self):
        return "<File path=%r type=%r>" %(self.path, self.type)

def slavemap(slaves, cmd, *args):
    for slave in slaves:
        getattr(slave, cmd)(*args)

    return [ getattr(slave, "last_" + cmd)() for slave in slaves ]

def _check_file(file, slaves):
    # Compare 'file' across the slaves
    if file.type != "REG":
        # Ignore non-regular files... For now.
        return

    sizes = slavemap(slaves, "size", file.path)
    unique = index_of_uniqe_element(sizes)
    if unique is not None:
        problem_file = slaves[unique].full_path(file)
        return ( problem_file,
                "size %s != %s" %(sizes[unique], sizes[0]) )

    checksums = slavemap(slaves, "checksum", file.path)
    unique = index_of_uniqe_element(checksums)
    if unique is not None:
        problem_file = slaves[unique].full_path(file)
        return ( problem_file,
                 "checksum %s != %s" %(checksums[unique], checksums[0]) )

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
            yield ( problem_file,
                    problem_description,
                    slaves[0].full_path(file) )

def compare_directories(dirs):
    from proxies import LocalSlaveProxy
    slaves = [ LocalSlaveProxy(dir) for dir in dirs ]

    for problem in check(slaves):
        yield problem

    for slave in slaves:
        slave.shutdown()

def run_master(args, help):
    if len(args) != 2:
        help()
        return 1

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

def default_options():
    return obj((option, default) for
               (option, default, _, _, _) in ordered_options)

ordered_options = (
#   (name, default, short, long, help)
#    ("first1024", False, "-1", "--first-1024",
#        "Only check the first 1024 bytes of each file."),
#    ("show_progress", False, "-p", "--progress",
#        "Show a progress bar."),
    ("debug", False, "-d", "--debug",
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
