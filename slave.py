#!/usr/bin/env python
from __future__ import with_statement

from randchk import assert_dir

from hashlib import md5
from types import GeneratorType
from os import path

import os
import re
import stat
import shlex
import sys

def debug(msg):
    return
    sys.stderr.write("%d: %s\n" %(os.getpid(), msg))

def shellquote(s):
    s = s.replace('"', r'\"') # Escape any single-quotes
    if re.search(r"\s", s):
        # Only quote the string if it contains whitespace
        s = '"' + s + '"'
    return s

def shellunquote(s):
    return shlex.split(s)

class SerializationError(Exception):
    pass

def unserialize(s):
    lines = s.split("\n")
    if len(lines) > 1:
        return [ tuple(shellunquote(line)) for line in lines ]
    else:
        return tuple(shellunquote(lines[0]))

def serialize(obj, recurse=None):
    # Serialize a tuple which contains strings, or a list
    # which contains tuples.
    if isinstance(obj, GeneratorType) and recurse == None:
        return serialize(list(obj))

    elif isinstance(obj, list) and recurse == None:
        return "\n".join(serialize(item, "list") for item in obj)

    elif isinstance(obj, tuple) and recurse in (None, "list"):
        return " ".join(serialize(item, "tuple") for item in obj)

    if isinstance(obj, basestring) and recurse == "tuple":
        return shellquote(obj)

    else:
        raise SerializationError("Can't serialize %r" %(obj))

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
            self.outstream.write(result + "\n\n")
            self.outstream.flush()

    def run_command(self, command, args):
        command = command.upper() + "_command"
        try:
            result = getattr(self, command)(*args)
        except EnvironmentError, e:
            result = ("ERROR", e.filename, e.strerror)
        return serialize(result)

    def LISTDIR_command(self, directory):
        for name in os.listdir(self.path(directory)):
            yield ( file_type(self.path(directory, name)),
                    path.join(directory, name) )

    def CHECKSUM_command(self, file):
        file = self.path(file)
        return ("checksum", checksum(file))

    def HELLO_command(self):
        return ("hello", )

if __name__ == "__main__":
    debug("Child started")
    assert_dir(sys.argv[1])
    s = Slave(sys.argv[1])
    s.run()
