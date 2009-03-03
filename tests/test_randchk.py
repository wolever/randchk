#!/usr/bin/env nosetests

from ..randchk import randlist, assert_dir, randomly_walk_files, switchprefix

from nose.tools import assert_equal, assert_raises
import os
from os import path
from os.path import dirname

def sanewalk(dir):
    """ A sane version of os.walk, yielding just paths. """
    for (root, dirs, files) in os.walk(dir):
        for file in files:
            yield path.join(root, file)

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
    testdir = path.join(dirname(__file__), "test_randomly_walk_files")
    expected = set(sanewalk(testdir))
    actual = set(randomly_walk_files(testdir))
    assert_equal(expected, actual)

def test_switchprefix():
    assert_equal(switchprefix("foo", "blamo", "foo/bar"), "blamo/bar")
    assert_equal(switchprefix("blamo", "foo", "blamo/bar"), "foo/bar")
    assert_raises(AssertionError, switchprefix, "foo", "bar", "bar/baz")
