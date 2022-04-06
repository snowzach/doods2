FROM python:3.10.4-slim-bullseye

# Value will be appended to .bazelrc Can be used to set no-avx.
# Example: "build --copt=-mno-avx"
ARG bazelrc=""

# Bazel options.
ARG bazel_opts="--config=release_base --config=avx_linux --config=nogcp --config=nonccl"

# Build Bazel and TensorFlow CPU.
# TODO: Avoid building unused tensorflow features.
RUN apt update && \
	apt install -y --no-install-recommends \
		bazel-bootstrap git build-essential openjdk-11-jdk zip unzip && \
	cd / && \
	git clone --branch 4.2.1 --depth 1 https://github.com/bazelbuild/bazel && \
	cd /bazel && \
	bazel build "//src:bazel" --compilation_mode=opt && \
	apt purge -y bazel-bootstrap build-essential openjdk-11-jdk zip unzip --autoremove && \
	mv /bazel/bazel-bin/src/bazel /usr/bin/ && \
	rm -r /bazel && \
	\
	cd / && \
	git clone --branch r2.8 --depth 1 https://github.com/tensorflow/tensorflow.git && \
	apt install -y --no-install-recommends python3-dev gcc g++ && \
	pip install -U pip numpy wheel packaging && \
	cd /tensorflow && \
	printf "$bazelrc" >> .bazelrc && \
	bazel build $bazel_opts tensorflow/tools/pip_package:build_pip_package && \
	mkdir /tensorflow/out && \
	./bazel-bin/tensorflow/tools/pip_package/build_pip_package /tensorflow/out --cpu && \
	pip install /tensorflow/out/* --no-deps && \
	pip uninstall -y wheel packaging && \
	apt purge -y git python3-dev gcc g++ --autoremove && \
	rm -rf /var/lib/apt/lists/* && \
	rm /usr/bin/bazel && \
	rm -r /root/.cache && \
	rm -r /tensorflow


# Build libedgetpu the Makefile way.
RUN apt update && \
	apt install -y --no-install-recommends \
		git make libflatbuffers-dev xxd gcc g++ libabsl-dev libusb-1.0-0-dev && \
	cd / && \
	git clone --branch master --depth 1 https://github.com/google-coral/libedgetpu.git && \
	cd /libedgetpu && \
	git clone --branch r2.5 --depth 1 https://github.com/tensorflow/tensorflow.git && \
	cd /libedgetpu && \
	TFROOT=/libedgetpu/tensorflow make -f makefile_build/Makefile -j$(nproc) libedgetpu && \
	mv /libedgetpu/out/direct/k8/* /usr/lib/*-linux-gnu/ && \
	apt purge -y \
		git make libflatbuffers-dev xxd gcc g++ libabsl-dev libusb-1.0-0-dev && \
	rm -rf /var/lib/apt/lists/* && \
	rm -r /libedgetpu


# Install minimum amount of TensorFlow python dependencies.
RUN pip install absl-py==1.0.0 protobuf==3.20.0 \
	wrapt==1.14.0 opt_einsum==3.3.0 gast==0.5.3 \
	astunparse==1.6.3 termcolor==1.1.0 flatbuffers==2.0


# Install DOODS dependencies.
RUN apt update && apt install -y --no-install-recommends \
    wget curl gnupg libpng16-16 libavcodec58 libavformat58 \
		libswscale5 libgl1 libglib2.0-0 unzip && \
	rm -rf /var/lib/apt/lists/*

# Install PyTorch dependencies
ADD requirements.pytorch.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Install python libs
ADD requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt


COPY --from=docker.io/snowzach/doods2:base-config /opt/doods/models /opt/doods/models
COPY --from=docker.io/snowzach/doods2:base-config /opt/doods/config.yaml /opt/doods/config.yaml

WORKDIR /opt/doods

ADD . .

ENV TF_CPP_MIN_LOG_LEVEL 3

ENTRYPOINT ["python3", "main.py"]
CMD ["api"]
