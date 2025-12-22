import os
import sys


def bad_function():
    # unused variable and single-quoted string (ruff expects double quotes per config)
    unused_var = 42
    print('this uses single quotes')
    # undefined name (will be flagged by ruff as F821 when analyzed statically)
    result = not_defined_variable
    # multiple statements on one line (style violation)
    if True: print('inline statement')
    # very long line to trigger line-length issues in linters
    long_line = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."""
    return None


# trailing whitespace below: 
