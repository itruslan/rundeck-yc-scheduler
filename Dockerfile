# hadolint global ignore=DL3008,DL3013
ARG RUNDECK_VERSION=5.19.0

FROM rundeck/rundeck:${RUNDECK_VERSION}

SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]

USER root

COPY requirements.txt /tmp/

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        zip \
    && python3 -m pip install --no-cache-dir -r /tmp/requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/requirements.txt

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY plugin/ /tmp/plugin-build/yc-scheduler/

# Build yc-scheduler plugin zip.
# Rundeck requires: <plugin-name>/plugin.yaml and <plugin-name>/contents/ inside the zip.
WORKDIR /tmp/plugin-build

RUN mkdir -p /home/rundeck/libext \
    && zip -rq /home/rundeck/libext/yc-scheduler.zip yc-scheduler \
    && rm -rf /tmp/plugin-build \
    && chown -R "$(id -u rundeck):$(id -g rundeck)" /home/rundeck/libext

WORKDIR /home/rundeck

USER rundeck
