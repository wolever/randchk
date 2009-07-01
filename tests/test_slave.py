#!/usr/bin/env python
from nose.tools import assert_equal

from slave import shellquote, shellunquote

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
