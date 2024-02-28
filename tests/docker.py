import logging
from dataclasses import dataclass
from types import TracebackType
from typing import List, Literal, Optional, Type, Union

import docker


@dataclass
class DockerContainer:
    logger: logging.Logger
    build_context: str
    dockerfile_path: str
    client: docker.DockerClient = docker.from_env()
    image: Optional[docker.models.images.Image] = None
    container: Optional[docker.models.containers.Container] = None

    def build(self) -> str:
        self.logger.info("Building image...")

        assert self.image is None, "Image has already been built."

        self.image, logs = self.client.images.build(
            path=self.build_context,
            dockerfile=self.dockerfile_path,
            rm=True,
            pull=True,
        )

        for log in logs:
            self.logger.debug(log)

        self.logger.info(f"Built example image: {self.image.short_id}")

        return self.image.id

    def start(self) -> str:
        self.logger.info("Starting container...")

        assert self.image is not None, "Image has not been built."
        assert self.container is None, "Container has already been run."

        self.container = self.client.containers.run(
            self.image,
            remove=True,
            detach=True,
            tty=True,
        )

        return self.container.name

    def kill(self) -> None:
        self.logger.info("Killing container...")

        assert self.container is not None, "Container has not been run."

        self.container.kill()

        self.logger.info(f"Killed container: {self.container.name}")

        self.container = None

    def __enter__(self) -> "DockerContainer":
        self.build()
        self.start()
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
        if self.container is None:
            return False
        try:
            self.container.reload()
            return self.container.status == "running"
        except docker.errors.NotFound:
            self.container = None
            return False

    def exec(self, cmd: Union[str, List[str]]) -> None:
        self.logger.info(f"Running command: {cmd}...")

        assert self.is_alive(), "Container is not running."

        return_code, (stdout, stderr) = self.container.exec_run(
            cmd,
            tty=True,
            demux=True,
            stdout=True,
            stderr=True,
        )

        if stdout is not None:
            self.logger.debug(stdout)
        if stderr is not None:
            self.logger.warning(stderr)

        self.logger.info(f"Ran command: {cmd}...")

        assert (
            return_code == 0
        ), "Failed to execute command in container. Return code: {return_code}"
