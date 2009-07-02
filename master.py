#!/usr/bin/env python

from cStringIO import StringIO
from subprocess import Popen, PIPE

import atexit
import sys
import os

from slave import Slave, unserialize, serialize
from randchk import randlist, index_of_uniqe_element

def debug(msg):
    sys.stderr.write("%s\n" %(msg, ))

class SlaveEnvError(Exception):
    def __init__(self, slave, filename, strerror):
        Exception.__init__(self, "ENVERROR: %s: %r for %r (%s)"
                                  %(strerror, file, slave.last_cmd, slave.pid))
        self.slave = slave
        self.filename = filename
        self.strerror = strerror

file_types = [ "REG", "DIR", "LNK", "BLK", "CHR", "FIFO", "SOCK" ]

class File(object):
    __slots__ = [ 'path', 'type' ]
    def __init__(self, type, path):
        if type not in file_types:
            raise Exception("Invalid type: %r" %(type))
        self.type = type
        self.path = path

    def __repr__(self):
        return "<File path=%r type=%r>" %(self.path, self.type)

class SlaveProxy(object):
    def __init__(self, instream=sys.stdin, outstream=sys.stdout, pid=-1):
        self.instream = instream
        self.outstream = outstream
        self.pid = pid
        self.last_cmd = None
        self.hello()

    def recv(self):
        lines = []
        while True:
            line = self.instream.readline()

            if line == "":
                # Make sure that the child hasn't died
                print "Empty read from child %d. Oh no." %(self.pid)
                sys.exit(42)

            # Check to see if the line is blank (the command is finished)
            line = line.strip()
            if line == "": break

            # Append the line
            debug("%d> %s" %(self.pid, line))
            lines.append(line)

        # Finally, unserialize the result
        result = unserialize("\n".join(lines))

        # Result may be empty if, for example, it's an empty directory
        if result and result[0] == "ENVERROR":
            (_, file, strerror) = result
            raise SlaveEnvError(self, file, strerror)

        return result

    def recv_list(self):
        result = self.recv()
        # Lists with only one element in them will become tuples...
        # so turn them into a proper list.
        # The len(...) > 0 check ensures that we don't end up
        # with [ [ ] ].
        if type(result) == tuple and len(result) > 0:
            result = [ result ]
        return result

    def recv_one(self):
        result = self.recv()
        assert type(result) != list
        return result

    def send(self, *command):
        to_send = serialize(tuple(command))
        debug("%s< %s" %(self.pid, to_send))
        self.last_cmd = to_send
        self.outstream.write(to_send + "\n")
        self.outstream.flush()

    def hello(self):
        self.send("hello")
        assert self.recv_one()[0] == "hello"

    def listdir(self, directory):
        """ Lists the remote directory, reuturns a list of 'File' instances."""
        self.send("listdir", directory)
        list = self.recv_list()
        return [ File(f[0], f[1]) for f in list ]

    def checksum(self, file):
        self.send("checksum", file)

    def last_checksum(self):
        (command, checksum) = self.recv_one()
        assert command == "checksum"
        return checksum

    def shutdown(self):
        # Perform a graceful shutdown
        self.send("bye")

class basic_walker(object):
    def __init__(self, list, root="/"):
        # 'list' is a function which accepts a path and return a list of files.
        # currently it is assumed that this list will be in the form:
        #    [ ( type, path ), ... ]
        # where 'path' is the complete path:
        #    >>> x = list("/tmp/")[0]
        #    >>> x.path
        #    '/tmp/x.py'
        #    >>> x.type
        #    'REG'
        #    >>>
        self.list = list
        self.root = "/"

    def __iter__(self):
        files = list(self.list(self.root))
        while files:
            file = files.pop()
            if file.type == "DIR":
                files.extend(self.list(file.path))
                continue
            yield file

def _compare_file(file, slaves):
    # Compare 'file' across the slaves
    if file.type != "REG":
        # Ignore non-regular files... For now.
        return

    for slave in slaves:
        slave.checksum(file.path)

    checksums = [ slave.last_checksum() for slave in slaves ]
    unique = index_of_uniqe_element(checksums)
    if unique is not None:
        # XXX: Need to include which slave this is...
        return ( file.path, "bad_checksum" )

    return None

def compare_file(file, slaves):
    try:
        return _compare_file(file, slaves)
    except SlaveEnvError, e:
        return ( e.filename, e.strerror )

def check_directories(dirs, walker=basic_walker):
    slaves = [ fork_slave(dir) for dir in dirs ]

    for file in walker(slaves[0].listdir):
        error = compare_file(file, slaves)
        if error is not None:
            yield error

    for slave in slaves:
        slave.shutdown()

def fork_slave(root):
    # Forks, starting a Slave, then returns a SlaveProxy connected to the
    # Slave's pipes

    p = Popen(["./slave.py", root], stdin=PIPE, stdout=PIPE)

    # Close the slaves pipes and wait for them to exit before we can exit
    def wait_for_slave():
        print "Waiting for slave %d to exit..." %(p.pid),
        p.stdin.close()
        p.stdout.close()
        p.wait()
        print "Done."
    atexit.register(wait_for_slave)

    return SlaveProxy(p.stdout, p.stdin, p.pid)

print "\n".join(map(repr, check_directories(["/tmp/", "/tmp/"])))
