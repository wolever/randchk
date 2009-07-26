import os
import sys

from .options import options

def debug(msg):
    if not options.debug:
        return

    if options.slave:
        msg = "%d: %s" %(os.getpid(), msg)
    sys.stderr.write("%s\n" %(msg, ))
