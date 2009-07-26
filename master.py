from __future__ import division

from utils import index_of_uniqe_element
from walkers import basic_walker
from options import options

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

def run_check(slaves, check, file):
    """ Run a check on slaves and return tuple with an error, or None. """
    # Run the check across the slaves
    results = slavemap(slaves, check, file.path)
    # Find out if any of them are different
    unique = index_of_uniqe_element(results)
    if unique is not None:
        # Figure out which file caused the problem
        problem_file = slaves[unique].full_path(file)
        return ( problem_file,
                 "%s %s != %s" %(check, results[unique], results[0]) )
    # If there is no error, we're done!
    return None

def _check_file(file, slaves):
    # Compare 'file' across the slaves
    if file.type != "REG":
        # Ignore non-regular files... For now.
        return

    for check in ("size", "checksum"):
        error = run_check(slaves, check, file)
        if error: return error

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

if __name__ == "__main__":
    print "master.py should not be run directly - use `randchk.py`"
