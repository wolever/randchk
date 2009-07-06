# If this file is run through nose, .. will automatically be added to sys.path.
from randchk import *
import randchk

from utils import randlist, assert_dir

from re import match
from glob import glob
from nose.tools import assert_equal, assert_raises, nottest
from os import path
from os import walk as oswalk
from os.path import dirname

def sanewalk(dir):
    """ A sane version of os.walk, yielding just paths. """
    for (root, dirs, files) in oswalk(dir):
        for file in files:
            yield path.join(root, file)

def helper_dir(name):
    """ Return the name of a subdirectory of this test directory. """
    return path.join(dirname(__file__), name)

def test_randlist():
    # Check that itering over the list works, even when items are being added
    rl = randlist([1,2])
    actual = set()
    for r in rl:
        actual.add(r)
        if len(actual) == 1:
            rl.append(3)
    assert_equal(actual, set([1,2,3]))

def test_index_of_uniqe_element():
    tests = (
        ([1], None),
        ([1, 1], None),
        ([1, 2], 1),
        ([2, 1], 1))
    for (input, expected) in tests:
        actual = index_of_uniqe_element(input)
        assert_equal(actual, expected)

def test_assert_dir():
    assert_dir('.')
    assert_raises(AssertionError, assert_dir, __file__)

def test_random_file_walker():
    # XXX: Fix this one.
    from nose.plugins.skip import SkipTest
    raise SkipTest()
    testdir = helper_dir("randomly_walk_files_helper")
    expected = set(sanewalk(testdir))
    actual = set(random_file_walker(testdir))
    assert_equal(expected, actual)

def directory_tests():
    # Note that glob is smart about expanding slashes so this will work as
    # expected on Windows
    for dir in glob(helper_dir("test_*/")):
        yield (run_directory_test, dir)

@nottest
def run_directory_test(directory):
    # Set the description of this function so Nose will give it a sensible name
    readme = open(path.join(directory, "README")).read()

    # Problem descriptions have two parts: a file name and a pattern which
    # should be part of the description.  They look like this:
    #     Problem: path/to/problem/file, pattern in the description
    def do_problem(line):
        """ Parse a "problem" line, returning (file, pattern). """
        parts = [part.strip() for part in line.split(",")]
        assert len(parts) == len(filter(None, parts)), \
               "Invalid 'Problem:' line: " + line
        return parts

    def do_options(line):
        """ Parse an "options" line, returning nothing. """
        import sys
        old_argv = sys.argv
        sys.argv = [ old_argv[0] ] + line.split()
        (_, _, new_options) = parse_options()
        randchk.options = default_options()
        randchk.options.update(new_options)
        sys.argv = old_argv

    expected_problems = []
    for line in readme.splitlines():
        line = line.split(": ", 1)
        if len(line) != 2:
            continue

        (header, rest) = line
        if header == "Problem":
            expected_problems.append(do_problem(rest))
        elif header == "Options":
            do_options(rest)

    # These are the directories which will be passed to compare_directories.
    # They are ordered alphabetically, so let's hope the "canonical"
    # directory is first.
    test_directories = sorted(glob(path.join(directory, "*/")))

    old_argv0 = sys.argv[0]
    try:
        # Fake argv[0] so we can fork() properly
        sys.argv[0] = "../randchk.py"
        # Actually run the code
        actual_problems = list(compare_directories(test_directories))
    finally:
        sys.argv[0] = old_argv0

    print "Expected problems:"
    print " - " + "\n - ".join(", ".join(p) for p in expected_problems)

    for (problem_file, problem_description, _) in actual_problems:
        found = False
        for (eid, (e_file, e_description)) in enumerate(expected_problems):
            # We only check that the problem file *ends* with the expected file
            # (makes life a bit easier, I think) 
            if not problem_file.endswith(e_file): continue
            assert e_description in problem_description, \
                   "Expected description, %r, not in actual description, %r." \
                    %(e_description, problem_description)
            expected_problems.pop(eid)
            found = True
            break

        assert found, "Unexpected problem encountered: %s: %s" \
                      %(problem_file, problem_description)

    # By now the expected_problems list should be empty
    assert expected_problems == [], \
           ("Expected problem(s) not encountered: " +
            ", ".join(desc for (_, desc) in expected_problems))
