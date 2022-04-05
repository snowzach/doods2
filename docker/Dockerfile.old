ARG TAG=amd64
FROM docker.io/snowzach/doods2:base-$TAG as base

COPY --from=docker.io/snowzach/doods2:base-config /opt/doods/models /opt/doods/models
COPY --from=docker.io/snowzach/doods2:base-config /opt/doods/config.yaml /opt/doods/config.yaml

# Create the doods user - need to be root to work with edgetpu
# RUN useradd -m -s /bin/bash -d /opt/doods doods
# USER doods

WORKDIR /opt/doods

ADD . .

ENV TF_CPP_MIN_LOG_LEVEL 3

ENTRYPOINT ["python3", "main.py"]
CMD ["api"]
