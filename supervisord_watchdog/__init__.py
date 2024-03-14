"""
A Python package which monitors the state of supervisord processes, and
terminates the container if any of the processes crash, if any of the critical
processes terminate, and optionally if all processes have terminated.
"""

import contextlib
from importlib.metadata import PackageNotFoundError, version

contextlib.suppress(PackageNotFoundError)

# Try and expose __version__, as per PEP396.
__version__ = version(__name__)
