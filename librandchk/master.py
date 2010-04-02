from __future__ import division

from .exceptions import FileIntegrityError
from .options import options
from .utils import index_of_uniqe_element
from .walkers import random_walker
from .File import File
from .proxies import LocalSlaveProxy, SlaveEnvError

def slavemap(slaves, cmd, *args):
    for slave in slaves:
        getattr(slave, cmd)(*args)

    return [ slave.recv_one() for slave in slaves ]

def run_check(slaves, check, file):
    """ Run a check on slaves and return tuple with an error, or None. """
    # Run the check across the slaves
    results = slavemap(slaves, check, file)

    # Check to see if any of the results were an error
    results_without_error = []
    for result in results:
        cmd = result[0]
        if "ERROR" in cmd:
            yield result[1:]
            continue

        assert cmd == check, "Unexpected command: %r" %(cmd, )
        results_without_error.append(result[1])

    # Check to make sure there are at least two results which *didn't* error out
    if len(results_without_error) < 2:
        return

    # Ignore the error'd results
    results = results_without_error

    # Find out if any of them are different
    unique = index_of_uniqe_element(results)
    if unique is not None:
        # Figure out which file caused the problem
        problem_file = slaves[unique].full_path(file)
        yield ( problem_file,
                "%s %s != %s" %(check, results[unique], results[0]) )
    # If there is no error... We're done!

def check_file(file, slaves):
    """ Check 'file' across 'slaves'.
        Returns a tuple '(file, description)' if any file causes an error. """
    # Compare 'file' across the slaves
    if file.type != "REG":
        # Ignore non-regular files... For now.
        return

    got_error = False
    for check in ("size", "checksum"):
        for error in run_check(slaves, check, file):
            got_error = True
            yield error

        # If we get an error, don't continue on to the next check
        if got_error:
            break

    # All done!

def check(slaves, walker_cls=random_walker):
    """ Start checking that the files seen by 'slaves' are identical. """

    walker = walker_cls()
    walker.add([ File("DIR", "/") ])

    for file in walker:
        if options.verbose:
            print file.path.lstrip('/')

        if file.type == "DIR":
            dir = file
            file_lists = []
            
            # Ask all the slaves to list this directory
            for slave in slaves:
                file_list = slave.listdir(dir)
                # Note: I'm using tuples to signal 'error'... Not great,
                #       but it's on the list of things to fix.
                if isinstance(file_list, tuple):
                    error = file_list
                    # If any error out (for example, because the directory
                    # is not executable), yield the error and move on
                    yield ( error[0],
                            error[1],
                            slaves[0].full_path(dir))

                    # If the slave that errored out is the canonical slave...
                    if slave is slaves[0]:
                        # ... then don't bother with checking the rest of the
                        # slaves. They won't tell us anything interesting.
                        break

                file_lists.append(( set(file_list), slave ))

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
            for error in check_file(file, slaves):
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
