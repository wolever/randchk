#!/usr/bin/env python
from nose.tools import assert_equal

from utils import shellquote, shellunquote, serialize, unserialize, \
                  SerializationError

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
