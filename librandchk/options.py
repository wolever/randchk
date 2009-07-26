from optparse import OptionParser

from .utils import obj

def parse_options():
    # Parse the command line arguments
    parser = OptionParser(usage = "usage: %prog [options] CANONICAL CHECK...\n"
        "\tRandomly checksum files in CANONICAL, comparing them to the same\n"
        "\tfile in each CHECK ensuring that they are the same.")

    for (name, _, short, long, help) in ordered_options:
        parser.add_option(short, long, action="store_true",
                          dest=name, help=help)

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
               (option, default, _, _, _) in ordered_options)

ordered_options = (
#   (name, default, short, long, help)
    ("first1024", False, "-1", "--first-1024",
        "Only check the first 1024 bytes of each file."),
#    ("show_progress", False, "-p", "--progress",
#        "Show a progress bar."),
    ("debug", False, "-d", "--debug",
        "Show debug information."),
    ("slave", False, "-s", "--slave",
        "(internal option)"),
)

options = default_options()
