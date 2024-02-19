import argparse
import logging
import subprocess
import sys
import time

from logging import Logger
from supervisor.childutils import listener  # type: ignore
from typing import List

# The set of events which can be received from supervisord
# which indicate that a process has exited unexpectedly.
process_crashed_events = set(
    [
        # The process exited with a non-expected exit code
        # (the set of expected exit codes for a program
        # can be configured in the supervisord.conf file)
        "PROCESS_STATE_FATAL",
        # This normally indicates an error in supervisord,
        # in which case we should assume that the process
        # is no longer running.
        "PROCESS_STATE_UNKNOWN",
    ]
)

# The set of events which can be received from supervisord
# which indicate that a process is no longer running.
process_no_longer_running_events = set(
    [
        # The process has exited normally.
        "PROCESS_STATE_EXITED",
        # The process has been stopped by supervisord
        "PROCESS_STATE_STOPPED",
        *process_crashed_events,
    ]
)


def kill_container(logger: Logger, termination_grace_period_seconds: float) -> None:
    # Send SIGTERM to init process (supervisord)
    # This signal will be passed down to all the supervisord services
    # and can be trapped by them, allowing them to gracefully shutdown,
    # and finally shutdown supervisord itself, which will terminate
    # the container.
    logger.info("Sending SIGTERM to init process...")
    subprocess.call(["/bin/sh", "-c", "kill -s TERM 1"])

    # We hope that the contaianer (and so by extension this Python script)
    # will be terminated during this sleep.
    time.sleep(termination_grace_period_seconds)

    # If we are still alive, then we send a SIGKILL to all processes,
    # which cannot be trapped and so will force them to shut down.
    logger.info("Termination grace period elapsed, sending SIGKILL to all processes...")
    subprocess.call(["/bin/sh", "-c", "kill -s KILL -1"])


def run(
    logger: Logger,
    termination_grace_period_seconds: float,
    critical_processes: List[str],
    should_terminate_if_all_processes_end: bool,
) -> None:
    logger.info(
        "Supervisord watchdog is running with critical processes: %r, terminate-if-all-processes-end: %r, termination grace period: %.2f",
        critical_processes,
        should_terminate_if_all_processes_end,
        termination_grace_period_seconds,
    )

    while True:
        # Block until an event occurs to one of the supervisord processes
        headers, body = listener.wait(sys.stdin, sys.stdout)
        body = dict([pair.split(":") for pair in body.split(" ")])

        logger.debug("Event occurred: %r", {"headers": headers, "body": body})
        event_name = headers["eventname"]

        try:
            if event_name in process_no_longer_running_events:
                logger.info("Process entered FATAL state...")
                process_name = body["processname"]
                if process_name in critical_processes:
                    logger.critical(
                        "Critical process %s has exited, killing container...",
                        process_name,
                    )
                    kill_container(logger, termination_grace_period_seconds)

                if event_name in process_crashed_events:
                    logger.critical(
                        "Process %s has crashed, killing container...",
                        process_name,
                    )
                    kill_container(logger, termination_grace_period_seconds)

                if should_terminate_if_all_processes_end:
                    # The output of this command looks like:
                    #
                    # <name>        <state>     <timestamp>
                    # <name>        <state>     <timestamp>
                    # <name>        <state>     <timestamp>
                    #
                    res = subprocess.check_output(
                        ["/usr/local/bin/supervisorctl", "status", "all"],
                    )
                    for line in res.decode("utf-8").strip().splitlines():
                        _, state, _ = line.split()
                        if (
                            f"PROCESS_STATE_{state}"
                            not in process_no_longer_running_events
                        ):
                            break
                    else:
                        logger.critical(
                            "All processes have exited, killing container..."
                        )
                        kill_container(logger, termination_grace_period_seconds)

        except Exception as e:
            logger.critical("Unexpected Exception: %s, killing container...", str(e))
            listener.fail(sys.stdout)

            # We assume that the watchdog process is critical to the container,
            # so if we get an unexpected exception, we kill the container.
            kill_container(logger, termination_grace_period_seconds)
        else:
            listener.ok(sys.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description="Supervisord watchdog")

    parser.add_argument(
        "--termination-grace-period",
        "-t",
        type=float,
        default=5.0,
        help="The number of seconds to wait for the container to shut down gracefully before sending SIGKILL to all processes.",
    )

    parser.add_argument(
        "--critical-process",
        "-c",
        type=str,
        default=[],
        nargs="+",
        help="\
The names of the critical supervisord processes which should be monitored by the watchdog. \
If any of these processes terminate, then the container will be terminated",
    )

    parser.add_argument(
        "--terminate-if-all-processes-end",
        "-T",
        action="store_true",
        help="If this argument is provided, then the container will be terminated if all supervisord processes terminate.",
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        help="The log level to use for the watchdog.",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )

    args = parser.parse_args()

    logging.basicConfig(
        stream=sys.stderr,
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(filename)s: %(message)s",
    )
    logger = logging.getLogger("supervisord-watchdog")
    run(
        logger,
        args.termination_grace_period,
        args.critical_process,
        args.terminate_if_all_processes_end,
    )
