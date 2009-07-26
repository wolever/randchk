from optparse import OptionParser

from .utils import obj

def parse_options():
    # Parse the command line arguments
    (parsed_options, args) = parser.parse_args()

    for option, default_value in parser.defaults.items():
        new_value = getattr(parsed_options, option)
        if default_value != new_value:
            options[option] = new_value

    return (parser, args)

def default_options():
    return obj((option, default) for
                option, default in parser.defaults.items())

parser = OptionParser(usage = "usage: %prog [options] CANONICAL CHECK...\n"
    "\tRandomly checksum files in CANONICAL, comparing them to the same\n"
    "\tfile in each CHECK ensuring that they are the same.")
option = parser.add_option

option("--exclude", action="append", metavar="PATTERN",
       dest="exclude", default=[],
       help="Exclude files matching PATTERN.")

option("--first-1024", action="store_true",
       dest="first1024", default=False,
       help="Only check the first 1024 bytes of each file.")

option("--debug", action="store_true",
       dest="debug", default=False,
       help="Show debug information.")

option("--slave", action="store_true",
       dest="slave", default=False,
       help="Run in slave mode (internal option)")

options = default_options()
