#!/bin/bash
set -o xtrace
set -e

for name in aarch64 armv7l amd64-noavx amd64 gpu; do
    docker buildx build --pull --push --build-arg TAG="$name" -t docker.io/snowzach/doods2:$name -f Dockerfile .
done

docker manifest push --purge docker.io/snowzach/doods2:latest
docker manifest create docker.io/snowzach/doods2:latest docker.io/snowzach/doods2:armv7l docker.io/snowzach/doods2:aarch64 docker.io/snowzach/doods2:amd64-noavx
docker manifest push docker.io/snowzach/doods2:latest
