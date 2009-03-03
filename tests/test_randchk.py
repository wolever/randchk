# If this file is run through nose, .. will automatically be added to sys.path.
from randchk import *

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


def test_assert_dir():
    assert_dir('.')
    assert_raises(AssertionError, assert_dir, __file__)

def test_randomly_walk_files():
    testdir = helper_dir("randomly_walk_files_helper")
    expected = set(sanewalk(testdir))
    actual = set(randomly_walk_files(testdir))
    assert_equal(expected, actual)

def test_switchprefix():
    assert_equal(switchprefix("foo", "blamo", "foo/bar"), "blamo/bar")
    assert_equal(switchprefix("blamo", "foo", "blamo/bar"), "foo/bar")
    assert_raises(AssertionError, switchprefix, "foo", "bar", "bar/baz")

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
    def parse_problem(line):
        """ Parse a "problem" line, returning (file, pattern). """
        assert line.startswith("Problem:")
        parts = [part.strip() for part in line[len("Problem:"):].split(",")]
        assert len(parts) == len(filter(None, parts)), \
               "Invalid 'Problem:' line: " + line
        return parts

    expected_problems = [parse_problem(line) for line in readme.splitlines()
                         if line.startswith("Problem:")]
   
    # These are the directories which will be passed to check_directories.
    # They are ordered alphanumerically, so let's hope the "canonical"
    # directory is first.
    test_directories = sorted(glob(path.join(directory, "*/")))
    problems = list(check_directories(test_directories))

    for (_, problem_file, problem_description) in problems:
        found = False
        for (eid, (e_file, e_description)) in enumerate(expected_problems):
            # We only check that the problem file *ends* with the expeced file
            # (makes life a bit easier, I think) 
            if not problem_file.endswith(e_file): continue
            found = True
            assert e_description in problem_description, \
                   "Expected description, %r, not in actual description, %r." \
                    %(e_description, problem_description)
            expected_problems.pop(eid)
            break

        assert found, "Unexpected problem encountered: %s: %s" \
                      %(problem_file, problem_description)
