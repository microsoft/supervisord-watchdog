"""
A Python package which monitors the state of supervisord processes, and
terminates the container if any of the critical processes terminate,
if any of the processes crash, and optionally if all processes have terminated.
"""

from pkg_resources import DistributionNotFound, get_distribution

# Try and expose __version__, as per PEP396.
try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass
