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

from utils import obj

def debug(msg):
    if not options.debug:
        return

    if options.slave:
        msg = "%d: %s" %(os.getpid(), msg)
    sys.stderr.write(msg + "\n")

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
    """ Check 'file' across 'slaves'. """
    try:
        return _compare_file(file, slaves)
    except SlaveEnvError, e:
        return ( e.filename, "env_error " + e.strerror )

def check_directories(dirs, walker=basic_walker):
    slaves = [ fork_slave(dir) for dir in dirs ]

    for file in walker(slaves[0].listdir):
        error = compare_file(file, slaves)
        if error is not None:
            yield error

    for slave in slaves:
        slave.shutdown()

def default_options():
    return obj((option, default) for
               (option, default, _, _, _) in ordered_options)

def fork_slave(root):
    """ Forks, starting a Slave, then returns a SlaveProxy connected to the
        Slave's pipes. """

    p = Popen([sys.argv[0], "--slave", root], stdin=PIPE, stdout=PIPE)

    # Close the slaves pipes and wait for them to exit before we can exit
    def wait_for_slave():
        debug("Waiting for slave %d to exit..." %(p.pid))
        p.stdin.close()
        p.stdout.close()
        p.wait()
        debug("Done.")
    atexit.register(wait_for_slave)

    return SlaveProxy(p.stdout, p.stdin, p.pid)

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
    (parser, args, new_options) = parse_options()
    options.update(new_options)

    if len(args) != 2:
        parser.print_help()
        sys.exit(1)

    for (canonical_file, problem_file, description) in check_directories(args):
        print "%s: %s (%s)" %(problem_file, description, canonical_file)
