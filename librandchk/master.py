from __future__ import division

from .options import options
from .utils import index_of_uniqe_element
from .walkers import basic_walker

class File(object):
    """ Represents the relative path to a file.
        In other words, a File does not know which slave it is associated with.
        Or, a File represents a file which should be common to all slaves. """

    # We could have a lot of Files, so define which slots we'll be using.
    __slots__ = [ '_type', '_path', '_hashcode' ]

    types = [ "REG", "DIR", "LNK", "BLK", "CHR", "FIFO", "SOCK" ]

    def __init__(self, type, path):
        if type not in File.types:
            raise Exception("Invalid type: %r" %(type))
        self._hashcode = None
        self._type = type
        self._path = path

    @property
    def type(self):
        return self._type

    @property
    def path(self):
        return self._path

    def __hash__(self):
        if self._hashcode is None:
            self._hashcode = ( self.type, self.path ).__hash__()
        return self._hashcode

    def __eq__(self, other):
        if not isinstance(other, File):
            return false
        return other.type == self.type and other.path == self.path

    def __repr__(self):
        return "<File path=%r type=%r>" %(self.path, self.type)

def slavemap(slaves, cmd, *args):
    for slave in slaves:
        getattr(slave, cmd)(*args)

    return [ getattr(slave, "last_" + cmd)() for slave in slaves ]

def run_check(slaves, check, file):
    """ Run a check on slaves and return tuple with an error, or None. """
    # Run the check across the slaves
    results = slavemap(slaves, check, file)
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

def check(slaves, walker_cls=basic_walker):
    """ Start checking that the files seen by 'slaves' are identical. """

    walker = walker_cls()
    walker.add([ File("DIR", "/") ])

    for file in walker:
        if file.type == "DIR":
            dir = file
            lists = [ (set(slave.listdir(dir)), slave) for slave in slaves ]
            canonical_list, canonical_slave = lists[0]
            for other_list, slave in lists[1:]:
                if other_list != canonical_list:
                    for file in (canonical_list - other_list):
                        # Files which are only in canonical
                        yield ( slave.full_path(file),
                                "File in source but not in backup",
                                canonical_slave.full_path(file) )

                    for file in (other_list - canonical_list):
                        # Files which are in the other list but not canonical
                        yield ( canonical_slave.full_path(file),
                                "File in backup but not in source",
                                slave.full_path(file) )

            for other_list, _ in lists[1:]:
                canonical_list = canonical_list.intersection(other_list)
            walker.add( canonical_list )

        elif file.type == "REG":
            error = check_file(file, slaves)
            if error is not None:
                (problem_file, problem_description) = error
                yield ( problem_file,
                        problem_description,
                        slaves[0].full_path(file) )

        elif file.type == "LNK":
            link_targets = [ (slave.readlink(file), slave) for slave in slaves ]
            canonical_link, canonical_slave = link_targets[0]
            for other_link, slave in link_targets[1:]:
                if canonical_link != other_link:
                    yield ( slave.full_path(file),
                            "Symlinks do not match (%s != %s)"
                                % (canonical_link, other_link),
                            canonical_slave.full_path(file) )

def compare_directories(dirs):
    from proxies import LocalSlaveProxy
    slaves = [ LocalSlaveProxy(dir) for dir in dirs ]

    for problem in check(slaves):
        yield problem

    for slave in slaves:
        slave.shutdown()

if __name__ == "__main__":
    print "master.py should not be run directly - use `randchk.py`"
