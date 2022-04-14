ARG TAG=amd64
FROM docker.io/snowzach/doods2:base-$TAG as base

# Build libedgetpu the Makefile way.
RUN apt update && \
	apt install -y --no-install-recommends \
		git make libflatbuffers-dev xxd gcc g++ libabsl-dev libusb-1.0-0-dev && \
	cd / && \
	git clone --branch master --depth 1 https://github.com/google-coral/libedgetpu.git && \
	cd /libedgetpu && \
	git clone --branch r2.5 --depth 1 https://github.com/tensorflow/tensorflow.git && \
	TFROOT=/libedgetpu/tensorflow make -f makefile_build/Makefile -j$(nproc) libedgetpu && \
	mv /libedgetpu/out/direct/k8/* /usr/lib/*-linux-gnu/ && \
	apt purge -y \
		git make libflatbuffers-dev xxd gcc g++ libabsl-dev libusb-1.0-0-dev && \
	rm -rf /var/lib/apt/lists/* && \
	rm -r /libedgetpu

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
