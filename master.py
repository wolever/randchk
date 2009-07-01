#!/usr/bin/env python

from cStringIO import StringIO
from subprocess import Popen, PIPE

import atexit
import sys
import os

from slave import Slave, unserialize, serialize

def debug(msg):
    return
    sys.stderr.write("%s\n" %(msg, ))

class SlaveError(Exception):
    def __init__(self, slave, file, message):
        Exception.__init__(self, "ERROR: %s: %r for %r (%s)"
                                  %(message, file, slave.last_cmd, slave.pid))

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
            line = self.instream.readline().strip()
            debug("%d> %s" %(self.pid, line))
            if line == "": break
            lines.append(line)
        result = unserialize("\n".join(lines))

        # The result should always have a length of at least 1
        if result[0] == "ERROR":
            (_, file, message) = result
            raise SlaveError(self, file, message)

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
        """ Lists the remote directory, reuturns:
            [
                ( type, path ),
                ( 'DIR', '/tmp/' ),
                ( 'REG', '/tmp/foo' ),
            ] """
        self.send("listdir", directory)
        return self.recv()

    def checksum(self, file):
        self.send("checksum", file)

    def last_checksum(self):
        (command, checksum) = self.recv_one()
        assert command == "checksum"
        return checksum

    def shutdown(self):
        # Perform a graceful shutdown
        self.send("bye")

def check(canonical, backup):
    files = canonical.listdir("/")
    for (type, path) in files:
        if type == "DIR":
            print "Ignoring dir", path
        elif type == "REG":
            canonical.checksum(path)
            backup.checksum(path)
            checksums = canonical.last_checksum(), backup.last_checksum()
            print "Checksum of", path
            print "\t", ",".join(checksums)

    canonical.shutdown()
    backup.shutdown()

def fork_slave():
    # Forks, starting a Slave, then returns a SlaveProxy connected to the
    # Slave's pipes

    p = Popen(["./slave.py", "/tmp/"], stdin=PIPE, stdout=PIPE)

    # Close the slaves pipes and wait for them to exit before we can exit
    def wait_for_slave():
        print "Waiting for slave %d to exit..." %(p.pid),
        p.stdin.close()
        p.stdout.close()
        p.wait()
        print "Done."
    atexit.register(wait_for_slave)

    return SlaveProxy(p.stdout, p.stdin, p.pid)

check(fork_slave(), fork_slave())
