#!/usr/bin/env python

from subprocess import Popen, PIPE

import atexit
import sys
import os

from .debug import debug
from .master import File
from .utils import serialize, unserialize, randlist, index_of_uniqe_element

class SlaveEnvError(Exception):
    def __init__(self, slave, filename, strerror):
        Exception.__init__(self, "ENVERROR: %s: %r for %r (%s)"
                                  %(strerror, file, slave.last_cmd, slave.pid))
        self.slave = slave
        self.filename = filename
        self.strerror = strerror


class SlaveProxy(object):
    def __init__(self, base_path, instream=sys.stdin, outstream=sys.stdout, pid=-1):
        self.base_path = base_path
        self.instream = instream
        self.outstream = outstream
        self.pid = pid
        self.last_cmd = None
        self.hello()

    def full_path(self, to_file):
        """ Return the full path to file 'to_file' relative to this slave:
            >>> SlaveProxy("/foo/bar/").full_path(File("REG", "/baz"))
            '/foo/bar/baz'
            >>> """
        return os.path.join(self.base_path, to_file.path.lstrip("/"))

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
        debug(result)
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
        self.send("listdir", directory.path)
        list = self.recv_list()
        return [ File(f[0], f[1]) for f in list ]

    def checksum(self, file):
        self.send("checksum", file.path)

    def last_checksum(self):
        (command, checksum) = self.recv_one()
        assert command == "checksum"
        return checksum

    def readlink(self, file):
        self.send("readlink", file.path)
        (command, link) = self.recv_one()
        assert command == "readlink"
        return link

    def size(self, file):
        self.send("size", file.path)

    def last_size(self):
        (command, size) = self.recv_one()
        assert command == "size"
        return size

    def shutdown(self):
        # Perform a graceful shutdown
        self.send("bye")


class LocalSlaveProxy(SlaveProxy):
    def __init__(self, path):
        # Args which will be passed to fork()
        args = [sys.argv[0], "--slave"]
        # Add all the options (assuming, for now, options start with a '-'
        # and none of the options take an argument).
        args.extend( arg for arg in sys.argv if arg.startswith("-") )
        args.append(path)

        # Fork() and start the child
        child = Popen(args, stdin=PIPE, stdout=PIPE)
        self.child = child

        def ensure_child_is_closed():
            if self.child.returncode == None:
                self.shutdown()
        atexit.register(ensure_child_is_closed)

        SlaveProxy.__init__(self, path, child.stdout, child.stdin, child.pid)

    def shutdown(self):
        SlaveProxy.shutdown(self)

        debug("Waiting for %d to exit..." %(self.child.pid))
        self.child.stdin.close()
        self.child.stdout.close()
        self.child.wait()
        debug("Done: %d exited with %s" %(self.child.pid, self.child.returncode))
