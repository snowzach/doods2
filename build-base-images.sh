#!/bin/bash

# Setup QEMU if needed
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# Build the docker images
docker buildx build --push --platform linux/arm/v7 -f Dockerfile.base.armv7l --tag docker.io/snowzach/doods2:base-armv7l .
docker buildx build --push --platform linux/arm64/v8 -f Dockerfile.base.aarch64 --tag docker.io/snowzach/doods2:base-aarch64 .
docker build -f Dockerfile.base.amd64-noavx --tag docker.io/snowzach/doods2:base-amd64-noavx .
docker push docker.io/snowzach/doods2:base-amd64-noavx
docker build -f Dockerfile.base.amd64 --tag docker.io/snowzach/doods2:base-amd64 .
docker push docker.io/snowzach/doods2:base-amd64
docker build -f Dockerfile.base.gpu --tag docker.io/snowzach/doods2:gpu .
docker push docker.io/snowzach/doods2:gpu

# Build the base config image
docker build -f Dockerfile.base.config --tag docker.io/snowzach/doods2:base-config .
docker push docker.io/snowzach/doods2:base-config
