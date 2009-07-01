#!/usr/bin/env python

from cStringIO import StringIO
from subprocess import Popen, PIPE

import sys
import os

from slave import Slave

class SlaveProxy(object):
    def __init__(self, instream=sys.stdin, outstream=sys.stdout, pid=-1):
        self.instream = instream
        self.outstream = outstream
        self.pid = pid
        self.hello()

    def recv(self):
        result = []
        while True:
            line = self.instream.readline().strip()
            print "From %d: %s" %(self.pid, line)
            if line == "": break
            result.append(line)
        return result

    def recv_one(self):
        result = self.recv()
        assert len(result) == 1
        return result[0]

    def send(self, command, *args):
        to_send = "%s %s\n" %(command, " ".join(args))
        print "To %s: %s" %(self.pid, to_send)
        self.outstream.write(to_send)
        self.outstream.flush()

    def hello(self):
        self.send("hello")
        assert self.recv_one() == "hello"

    def listdir(self, directory):
        """ Lists the remote directory, reuturns:
            [
                [ type, path ],
                [ 'DIR', '/tmp/' ],
                [ 'REG', '/tmp/foo' ],
            ] """
        self.send("listdir", directory)
        return map(lambda result: result.split(None, 1), self.recv())

    def checksum(self, file):
        self.send("checksum", file)

    def last_checksum(self):
        last = self.recv_one()
        (command, checksum, file) = last.split(None, 2)

def check(canonical, backup):
    files = canonical.listdir("/")
    for (type, path) in files:
        if type == "DIR":
            print "Ignoring dir", path
        elif type == "REG":
            canonical.checksum(path)
            backup.checksum(path)
            print path
            print "\t", canonical.last_checksum(), backup.last_checksum()

def fork_slave():
    # Forks, starting a Slave, then returns a SlaveProxy connected to the
    # Slave's pipes
    p = Popen(["./slave.py", "/tmp/"], stdin=PIPE, stdout=PIPE)
    return SlaveProxy(p.stdout, p.stdin, p.pid)

check(fork_slave(), fork_slave())
