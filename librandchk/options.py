from optparse import OptionParser

from .utils import obj

def parse_options():
    # Parse the command line arguments
    (parsed_options, args) = parser.parse_args()

    new_options = obj()

    # Load the options which have been changed into new_options
    for option, default_value in parser.defaults.items():
        new_value = getattr(parsed_options, option)
        if default_value != new_value:
            new_options[option] = new_value

    return (parser, args, new_options)

def default_options():
    return obj((option, default) for
                option, default in parser.defaults.items())

parser = OptionParser(usage = "usage: %prog [options] CANONICAL CHECK...\n"
    "\tRandomly checksum files in CANONICAL, comparing them to the same\n"
    "\tfile in each CHECK ensuring that they are the same.")
option = parser.add_option

option("-1", "--first-1024", action="store_true", dest="first1024",
       help="Only check the first 1024 bytes of each file.")

option("-d", "--debug", action="store_true", dest="debug",
       help="Show debug information.")

option("-s", "--slave", action="store_true", dest="slave",
       help="Run in slave mode (internal option)")

options = default_options()
