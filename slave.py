#!/usr/bin/env python
from __future__ import with_statement

from randchk import assert_dir

import sys
import os
import stat
from hashlib import md5

def debug(msg):
    sys.stderr.write("%d: %s\n" %(os.getpid(), msg))

def serialize(obj):
    if isinstance(obj, basestring):
        return obj
    elif hasattr(obj, '__iter__'):
        return "\n".join(serialize(item) for item in obj)
    else:
        raise Exception("Can't serialize %r" %(obj))

def checksum(file):
    with open(file) as f:
        sum = md5()
        data = f.read(1024)
        while data:
            sum.update(data)
            data = f.read(1024)
        return sum.hexdigest()

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
        self.instream = instream
        self.outstream = outstream

        assert_dir(root)
        self.root = os.path.normpath(root)

    def path(self, file):
        file = os.path.normpath(file)
        return os.path.join(self.root, file)

    def run(self):
        while True:
            debug("Waiting for input...")
            line = self.instream.readline().strip().split()
            debug("Read: %r" %(line))
            (command, args) = (line[0], line[1:])
            result = self.run_command(command, args)
            self.outstream.write(result + "\n\n")
            self.outstream.flush()

    def run_command(self, command, args):
        command = command.upper() + "_command"
        result = getattr(self, command)(*args)
        return serialize(result)

    def LISTDIR_command(self, directory):
        directory = self.path(directory)
        for name in os.listdir(directory):
            name = os.path.join(directory, name)
            yield file_type(name) + " " + name

    def CHECKSUM_command(self, file):
        return " ".join([ "checksum", checksum(self.path(file)), file ])

    def HELLO_command(self):
        return "hello"

if __name__ == "__main__":
    debug("Child started")
    assert_dir(sys.argv[1])
    s = Slave(sys.argv[1])
    s.run()
