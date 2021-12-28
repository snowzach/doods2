#!/bin/bash

for name in aarch64 armv7l amd64-noavx amd64 gpu; do
    docker build --build-arg TAG="$name" -t docker.io/snowzach/doods2:$name -f Dockerfile .
    if [[ "$1" == "push" ]]; then
        docker push docker.io/snowzach/doods2:$name
    fi
done
