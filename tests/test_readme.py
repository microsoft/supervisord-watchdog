import re

from supervisord_watchdog.watchdog import _create_argument_parser


# Replace "usage: any-program-name" in the input string with
# "usage: some-other-program-name"
def replace_program_name(input_string, new_program_name):
    return re.sub(r"usage: ([^\s]+)", f"usage: {new_program_name}", input_string)


# Test to make sure that the `Usage` section of this repo's README
# doesn't get out of date.
def test_readme_help():
    program_name = "supervisord_watchdog"

    with open("README.md") as fp:
        readme = replace_program_name(fp.read(), program_name)

    usage = replace_program_name(_create_argument_parser().format_help(), program_name)

    assert usage in readme
