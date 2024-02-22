import subprocess
import logging
import time

from typing import IO, Optional, Type, Literal
from types import TracebackType

CONTAINER_START_WAIT_TIME_SECONDS = 5


class DockerContainer:

    logger: logging.Logger
    build_context: str
    dockerfile_path: str
    image_name: Optional[str]
    container_name: Optional[str]

    def __init__(
        self, logger: logging.Logger, build_context: str, dockerfile_path: str
    ):
        self.logger = logger
        self.build_context = build_context
        self.dockerfile_path = dockerfile_path
        self.image_name = None
        self.container_name = None

    def _log_pipe(self, pipe: Optional[IO[bytes]], level: int) -> None:
        assert pipe is not None, "Pipe is not open."
        for line in iter(pipe.readline, b""):
            self.logger.log(level, line.decode("utf-8").strip())

    def build(self) -> str:
        self.logger.info("Building example image...")

        assert self.image_name is None, "Image has already been built."

        build = subprocess.Popen(
            ["docker", "build", self.build_context, "-f", self.dockerfile_path, "-q"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return_code = build.wait()
        self._log_pipe(build.stderr, logging.WARN)

        assert return_code == 0, "Failed to build example image."

        assert build.stdout is not None, "Failed to capture build output."
        self.image_name = build.stdout.readlines()[-1].decode("utf-8").strip()

        assert (
            self.image_name is not None
        ), "Failed to parse image name from build output."

        self.logger.info(f"Built example image: {self.image_name}")

        return self.image_name

    def start(self) -> str:
        self.logger.info("Starting example container...")

        assert self.image_name is not None, "Image has not been built."
        assert self.container_name is None, "Container has already been run."

        run = subprocess.Popen(
            ["docker", "run", "--rm", "-d", self.image_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self._log_pipe(run.stderr, logging.ERROR)

        return_code = run.wait()

        assert return_code == 0, "Failed to run example container."

        assert run.stdout is not None, "Failed to capture run output."
        self.container_name = run.stdout.read().decode("utf-8").strip()

        assert (
            self.container_name is not None
        ), "Failed to parse container name from run output."

        self.logger.info(f"Started example container: {self.container_name}")

        return self.container_name

    def kill(self) -> None:
        self.logger.info(f"Killing container: {self.container_name}")

        assert self.container_name is not None, "Container has not been run."

        kill = subprocess.Popen(
            ["docker", "kill", self.container_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        return_code = kill.wait()
        self._log_pipe(kill.stdout, logging.DEBUG)
        self._log_pipe(kill.stderr, logging.ERROR)

        assert return_code == 0, "Failed to kill container."

        self.logger.info(f"Killed container: {self.container_name}")

        self.container_name = None

    def __enter__(self) -> "DockerContainer":
        self.build()
        self.start()
        create_time = time.time()
        while time.time() - create_time < CONTAINER_START_WAIT_TIME_SECONDS:
            if self.is_alive():
                break
            time.sleep(1)
        else:
            raise Exception("Container did not start in time.")
        return self

    def __exit__(
        self,
        _exc_type: Optional[Type[BaseException]],
        _exc_value: Optional[BaseException],
        _traceback: Optional[TracebackType],
    ) -> Literal[False]:
        if self.is_alive():
            self.kill()
        return False

    def is_alive(self) -> bool:
        assert self.container_name is not None, "Container has not been run."
        inspect = subprocess.Popen(
            [
                "docker",
                "inspect",
                "--format",
                "{{.State.Running}}",
                self.container_name,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        return_code = inspect.wait()

        if return_code != 0:
            return False

        assert inspect.stdout is not None, "Failed to capture inspect output."
        return inspect.stdout.read().decode("utf-8").strip() == "true"

    def exec(self, cmd: str) -> None:
        assert self.container_name is not None, "Container has not been run."

        exec = subprocess.Popen(
            ["docker", "exec", self.container_name, "sh", "-c", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        return_code = exec.wait()
        self._log_pipe(exec.stdout, logging.DEBUG)
        self._log_pipe(exec.stderr, logging.ERROR)

        assert return_code == 0, "Failed to execute command in container."
