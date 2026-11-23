#!/bin/sh
# uv vs pip: one container with both tools pinned (Dockerfile), 2 CPUs and 4 GB, venvs and caches on the container
# disk. Downloads come from PyPI over the same internet connection for both, alternating order each round.
set -e
rm -rf data; mkdir -p data
MSYS_NO_PATHCONV=1 docker build -q -t uvpip . >/dev/null
MSYS_NO_PATHCONV=1 docker run --rm --cpus=2 --memory=4g -e PIP_ROOT_USER_ACTION=ignore -e PIP_DISABLE_PIP_VERSION_CHECK=1 \
  -v "$(pwd -W 2>/dev/null || pwd):/w" uvpip sh /w/bench.sh
