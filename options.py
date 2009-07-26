from utils import obj

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
