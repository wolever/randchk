from librandchk.File import File

from nose.tools import raises, assert_equal, assert_not_equal

@raises(AttributeError)
def test_file_immutability():
    f = File("DIR", "/")
    # Files are immutable, so this should raise an exception
    f.path = "/foo"

@raises(Exception)
def test_file_bad_type_check():
    # An exception should be raised if we're instanciating
    # File with a bad type
    File("BAD", "/")

def test_file_good_types():
    # All the 'good' types should work, though
    for type in File.types:
        File(type, "/")

def test_file_in_set():
    files = [ File("DIR", "/"), File("DIR", "/"),
              File("REG", "/"), File("DIR", "/x") ]

    files_set = set(files)
    # The first two files are identical, so the set should be the same if only
    # one of them is there and it shold only have 3 items
    assert_equal(files_set, set(files[1:]))
    assert_equal(len(files_set), 3)

def test_file_equality():
    assert_equal(File("DIR", "/"), File("DIR", "/"))
    assert_not_equal(File("REG", "/"), File("DIR", "/"))
    assert_not_equal(File("DIR", "/x"), File("DIR", "/y"))
