from __future__ import division

from .exceptions import FileIntegrityError
from .options import options
from .utils import index_of_uniqe_element
from .walkers import basic_walker
from .File import File
from .proxies import LocalSlaveProxy, SlaveEnvError

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
    try:
        return _check_file(file, slaves)
    except SlaveEnvError, e:
        return ( e.filename, "env_error " + e.strerror )
    except FileIntegrityError, e:
        return ( e.filename, "Integrity error: " + e.strerror )

def check(slaves, walker_cls=basic_walker):
    """ Start checking that the files seen by 'slaves' are identical. """

    walker = walker_cls()
    walker.add([ File("DIR", "/") ])

    for file in walker:
        if file.type == "DIR":
            dir = file
            file_lists = []
            
            # Ask all the slaves to list this directory
            for slave in slaves:
                try:
                    file_list = slave.listdir(dir)
                    file_lists.append(( set(file_list), slave ))
                except SlaveEnvError, e:
                    # If any error out (for example, because the directory
                    # is not executable), yield the error and move on
                    yield ( e.filename,
                            "env_error " + e.strerror,
                            slaves[0].full_path(dir))

                    # If the slave that errored out is the canonical slave...
                    if slave is slaves[0]:
                        # ... then don't bother with checking the rest of the
                        # slaves. They won't tell us anything interesting.
                        break

            # If the canonical slave errored out...
            if not file_lists:
                # ... then don't bother checking the rest. Just bail out and
                # start checking the next file.
                continue

            # Otherwise, continue on with the checking.
            canonical_list, canonical_slave = file_lists[0]
            for other_list, slave in file_lists[1:]:
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

            # Remove from the canonical list any files which appear in none
            # of the other slaves. For example, if the canonical list
            # if [ a, b, c ], and the other slaves are [ [ a, b ], [ b ] ],
            # we still want to check 'a' (because it is in at least one
            # of the slaves), but since none of the slaves have 'c', there is
            # no point in checking it again.

            # This is done by first building a union of all the other
            # file lists...
            other_lists_union = set()
            for other_list, _ in file_lists[1:]:
                other_lists_union.update(other_list)
            
            # ... then intersecting that with the canonical list.
            walker.add(canonical_list.intersection(other_lists_union))

        elif file.type == "REG":
            error = check_file(file, slaves)
            if error is not None:
                (problem_file, problem_description) = error
                yield ( problem_file,
                        problem_description,
                        slaves[0].full_path(file) )

        elif file.type == "LNK":
            link_targets = [ (slave.readlink(file), slave)
                             for slave in slaves ]
            canonical_link, canonical_slave = link_targets[0]
            for other_link, slave in link_targets[1:]:
                if canonical_link != other_link:
                    yield ( slave.full_path(file),
                            "Symlinks do not match (%s != %s)"
                                % (canonical_link, other_link),
                            canonical_slave.full_path(file) )

def compare_directories(dirs):
    slaves = [ LocalSlaveProxy(dir) for dir in dirs ]

    for problem in check(slaves):
        yield problem

    for slave in slaves:
        slave.shutdown()

if __name__ == "__main__":
    print "master.py should not be run directly - use `randchk.py`"
