import logging
import platform
import re

import pytest

from supervisord_watchdog.watchdog import _create_argument_parser

logger = logging.getLogger(__name__)


def replace_program_name(input_string, new_program_name):
    """
    Replace "usage: any-program-name" in the input string with
    "usage: some-other-program-name"
    """
    return re.sub(r"usage: ([^\s]+)", f"usage: {new_program_name}", input_string)


@pytest.mark.skipif(
    platform.python_version_tuple()[:2] != ("3", "9"),
    reason="The argparse help text changes between Python versions. "
    "We only need to test one version to make sure the README isn't out of date.",
)
def test_readme_help():
    """
    Test to make sure that the `Usage` section of this repo's README
    doesn't get out of date.
    """
    program_name = "supervisord_watchdog"

    with open("README.md") as fp:
        readme = replace_program_name(fp.read(), program_name)

    usage = replace_program_name(_create_argument_parser().format_help(), program_name)

    if usage not in readme:
        logger.error("The usage string in the README is out of date.")
        logger.error("Please update the README with the following usage string:")
        logger.error(usage)
        raise AssertionError()
