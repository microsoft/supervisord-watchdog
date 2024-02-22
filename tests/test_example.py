import time
import logging
from tests.docker import DockerContainer

logger = logging.getLogger(__name__)

WATCHDOG_MAX_REACTION_TIME_SECONDS = 5


# Basic integration test.
#
# We start the example container, kill the critical process,
# and then check that the container dies as expected.
def test_example_container() -> None:
    # Spin up the example container
    with DockerContainer(logger, ".", "example/Dockerfile") as container:
        # The container should stay alive for a while
        time.sleep(WATCHDOG_MAX_REACTION_TIME_SECONDS)
        assert container.is_alive()

        # Kill the critical process, proc.py
        container.exec("kill $(ps aux | grep proc.py | awk '{print $2}' | head -n 1)")

        # The container should then die on its own
        start_time = time.time()
        while time.time() - start_time < WATCHDOG_MAX_REACTION_TIME_SECONDS:
            if not container.is_alive():
                break
        else:
            raise AssertionError("Container did not die in time.")
