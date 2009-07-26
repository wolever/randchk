#!/usr/bin/env python
from nose.tools import assert_equal, assert_raises

from librandchk.utils import obj, SerializationError
from librandchk.utils import randlist, assert_dir, index_of_uniqe_element
from librandchk.utils import serialize, unserialize
from librandchk.utils import shellquote, shellunquote

def test_shellquote():
    tests = [
        [ 'simple_string', 'simple_string' ],
        [ 'with space', '"with space"' ],
        [ 'with"quote', r'with\"quote' ],
        [ 'quote" space', r'"quote\" space"' ],
    ]

    for test, expected in tests:
        # Test that the shell quoter properly quotes things
        assert_equal(shellquote(test), expected)
        # And then that the unquoter will read it back properly
        print expected
        assert_equal(shellunquote(expected), [ test ])

def test_serialize_simple():
    tests = [
        ('cmd', 'arg "0"', "arg '1'"),
        [ ('a', 'b'), ('a b', 'c d') ],
    ]

    for test in tests:
        print "Test:", test
        print "Serialized:", serialize(test)
        assert_equal(unserialize(serialize(test)), test)

def test_serialize_generator():
    def generator():
        yield ( "a", "b" )
        yield ( "c", "d" )

    assert_equal(serialize(generator()), serialize(list(generator())))

def test_serialize_numbers():
    assert_equal(serialize( (42, 42.0, 42L) ), "42 42.0 42")

def test_bad_serializers():
    tests = [
        "a plain string",
        [ [ "nested list" ] ],
        { "diction":"ary" },
        ( [ "list in tuple" ] ),
    ]

    for test in tests:
        try:
            assert not serialize(test)
        except SerializationError:
            pass

def test_obj():
    myobj = obj( {"foo": "foo"} )
    myobj.fourtytwo = 42

    assert_equal(myobj.foo, "foo")
    assert_equal(myobj.fourtytwo, 42)

    myobj.foo = "bar"
    assert_equal(myobj.foo, "bar")

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

def test_index_of_uniqe_element():
    tests = (
        ([1], None),
        ([1, 1], None),
        ([1, 2], 1),
        ([2, 1], 1))
    for (input, expected) in tests:
        actual = index_of_uniqe_element(input)
        assert_equal(actual, expected)
