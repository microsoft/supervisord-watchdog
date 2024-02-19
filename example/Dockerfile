# NOTE: The build context for this image should be the repository root.
#       E.g., build with `docker build . -f example/Dockerfile`

FROM ubuntu:22.04

RUN apt-get update -y

RUN apt-get install -y python3 python3-pip
RUN pip install supervisor

COPY example/supervisord.conf /etc/supervisord.conf

# You'll likely want to install supervisord_watchdog from PyPI
# rather than from a local wheel file
COPY dist/ /opt/dist
RUN pip install /opt/dist/*.whl

WORKDIR /app
COPY example/proc.py /app

ENTRYPOINT ["supervisord", "-c", "/etc/supervisord.conf"]