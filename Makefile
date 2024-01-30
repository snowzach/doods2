
VERSION=$(shell cat .current_version)

default:

buildx-setup:
	docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

docker-base-armv7l:
	docker buildx build --pull --push --platform linux/arm/v7 -f docker/Dockerfile.base.armv7l --tag docker.io/snowzach/doods2:base-armv7l .

docker-base-aarch64:
	docker buildx build --pull --push --platform linux/arm64/v8 -f docker/Dockerfile.base.aarch64 --tag docker.io/snowzach/doods2:base-aarch64 .

docker-base-amd64-noavx:
	docker buildx build --pull --push -f docker/Dockerfile.base.amd64-noavx --tag docker.io/snowzach/doods2:base-amd64-noavx .

docker-base-amd64:
	docker buildx build --pull --push -f docker/Dockerfile.base.amd64 --tag docker.io/snowzach/doods2:base-amd64 .

docker-base-amd64-gpu:
	docker buildx build --pull --push -f docker/Dockerfile.base.amd64-gpu --tag docker.io/snowzach/doods2:base-amd64-gpu .

docker-base: docker-base-armv7l docker-base-aarch64 docker-base-amd64-noavx docker-base-amd64 docker-base-amd64-gpu

docker-armv7l:
	docker buildx build --pull --push --build-arg TAG="armv7l" -f docker/Dockerfile -t docker.io/snowzach/doods2:armv7l .

docker-aarch64:
	docker buildx build --pull --push --build-arg TAG="aarch64" -f docker/Dockerfile -t docker.io/snowzach/doods2:aarch64 .

docker-amd64-noavx:
	docker buildx build --pull --push --build-arg TAG="amd64-noavx" -f docker/Dockerfile -t docker.io/snowzach/doods2:amd64-noavx .

docker-amd64:
	docker buildx build --pull --push --build-arg TAG="amd64" -f docker/Dockerfile -t docker.io/snowzach/doods2:amd64 .

docker-amd64-gpu:
	docker buildx build --pull --push --build-arg TAG="amd64-gpu" -f docker/Dockerfile -t docker.io/snowzach/doods2:amd64-gpu .

docker: docker-armv7l docker-aarch64 docker-amd64 docker-amd64-noavx docker-amd64-gpu
	docker manifest push --purge docker.io/snowzach/doods2:latest
	docker manifest create docker.io/snowzach/doods2:latest docker.io/snowzach/doods2:armv7l docker.io/snowzach/doods2:aarch64 docker.io/snowzach/doods2:amd64-noavx
	docker manifest push docker.io/snowzach/doods2:latest

docker-version:
	docker manifest push --purge docker.io/snowzach/doods2:${VERSION} || true
	docker manifest create docker.io/snowzach/doods2:${VERSION} docker.io/snowzach/doods2:armv7l docker.io/snowzach/doods2:aarch64 docker.io/snowzach/doods2:amd64-noavx
	docker manifest create --amend docker.io/snowzach/doods2:${VERSION}-armv7l docker.io/snowzach/doods2:armv7l
	docker manifest create --amend docker.io/snowzach/doods2:${VERSION}-aarch64 docker.io/snowzach/doods2:aarch64
	docker manifest create --amend docker.io/snowzach/doods2:${VERSION}-amd64-noavx docker.io/snowzach/doods2:amd64-noavx
	docker manifest create --amend docker.io/snowzach/doods2:${VERSION}-amd64 docker.io/snowzach/doods2:amd64
	docker manifest create --amend docker.io/snowzach/doods2:${VERSION}-amd64-gpu docker.io/snowzach/doods2:amd64-gpu
	docker manifest push docker.io/snowzach/doods2:${VERSION}-armv7l
	docker manifest push docker.io/snowzach/doods2:${VERSION}-aarch64
	docker manifest push docker.io/snowzach/doods2:${VERSION}-amd64-noavx
	docker manifest push docker.io/snowzach/doods2:${VERSION}-amd64
	docker manifest push docker.io/snowzach/doods2:${VERSION}-amd64-gpu

docker-config:
	# Build the base config image
	docker buildx build --pull --push -f docker/Dockerfile.base.config --tag docker.io/snowzach/doods2:base-config .
