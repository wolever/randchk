#!/usr/bin/env python
from __future__ import with_statement


from hashlib import md5
from os import path

import os
import re
import stat
import sys

from .debug import debug
from .options import options
from .utils import serialize, unserialize, assert_dir

def checksum(file):
    """ Checksum a file. """
    with open(file) as f:
        sum = md5()

        if '--first-1024' in sys.argv:
            debug("STUFF: %r" %( options ))
            debug("OPTIONS: %s" %( id(options) ))

        if options.first1024:
            # Only do one read
            data = f.read(1024)
            sum.update(data)

        else:
            # Read until the end
            data = f.read(1024)
            while data:
                sum.update(data)
                data = f.read(1024)

        return sum.hexdigest()

def file_size(file):
    """ Get a file's size. """
    return os.stat(file).st_size

def file_type(path):
    _types = {
        stat.S_IFREG: "REG",
        stat.S_IFDIR: "DIR",
        stat.S_IFLNK: "LNK",
        stat.S_IFBLK: "BLK",
        stat.S_IFCHR: "CHR",
        stat.S_IFIFO: "FIFO",
        stat.S_IFSOCK:"SOCK",
    }

    statinfo = os.lstat(path)[stat.ST_MODE]
    return _types[stat.S_IFMT(statinfo)]

class Slave(object):
    def __init__(self, root, instream=sys.stdin, outstream=sys.stdout):
        assert_dir(root)
        self.root = path.normpath(root)

        self.instream = instream
        self.outstream = outstream


    def path(self, *files):
        # path.join("/tmp", "/") == "/", not "/tmp/"
        # so we strip the leading "/" from everything:
        # path.join("/tmp", "") == "/tmp/"
        files = [ path.normpath(file).lstrip("/") for file in files ]
        return path.join(self.root, *files)

    def run(self):
        while True:
            debug("Waiting for input...")
            line = unserialize(self.instream.readline().strip())
            debug("Read: %r" %(line, ))

            if not line:
                debug("Empty read - going down.")
                return

            (command, args) = (line[0], line[1:])
            
            if command == "bye":
                debug("Got 'bye' - going down...")
                return

            result = self.run_command(command, args)
            result += "\n"
            if len(result) > 1:
                # Make sure that the result has a trailing newline
                result += "\n"
            self.outstream.write(result)
            self.outstream.flush()

    def run_command(self, command, args):
        command = command.upper() + "_command"
        try:
            result = getattr(self, command)(*args)
            return serialize(result)
        except EnvironmentError, e:
            # It's possible that, if a generator is returned, an exception
            # won't be raised until serialize starts to walk over it...
            # So we have to keep this call separate
            return serialize(("ENVERROR", e.filename, e.strerror))

    def LISTDIR_command(self, directory):
        for name in os.listdir(self.path(directory)):
            yield ( file_type(self.path(directory, name)),
                    path.join(directory, name) )

    def CHECKSUM_command(self, file):
        file = self.path(file)
        return ("checksum", checksum(file))

    def SIZE_command(self, file):
        file = self.path(file)
        return ("size", file_size(file))

    def HELLO_command(self):
        return ("hello", )

if __name__ == "__main__":
    print "slave.py should not be run directly - use `randchk.py --slave`"
