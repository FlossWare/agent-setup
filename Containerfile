# syntax=docker/dockerfile:1
# Fedora + Podman dogfood image for FlossWare coding-agent tooling.
FROM registry.fedoraproject.org/fedora:latest

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLOSSWARE_HOME=/opt/flossware \
    PATH=/opt/flossware/venv/bin:/usr/local/bin:$PATH

RUN dnf -y update && \
    dnf -y install \
      git python3 python3-devel python3-pip \
      gcc gcc-c++ make pkgconf-pkg-config \
      openssl-devel libffi-devel rust cargo ncurses-devel \
      findutils procps-ng && \
    dnf clean all && \
    rm -rf /var/cache/dnf

RUN python3 -m venv /opt/flossware/venv && \
    /opt/flossware/venv/bin/python -m pip install --upgrade pip setuptools wheel

ARG FLOSSWARE_RELEASE_REF=main
ARG CODING_AGENT_AI_REF=main

RUN git clone --depth 1 --branch "${CODING_AGENT_AI_REF}" \
      https://github.com/FlossWare/coding-agent-ai.git /opt/flossware/coding-agent-ai && \
    /opt/flossware/venv/bin/pip install \
      "/opt/flossware/coding-agent-ai[all,tui]"

COPY . /opt/flossware/coding-agent-setup
RUN /opt/flossware/venv/bin/python -m compileall -q /opt/flossware/coding-agent-setup/scripts/setup.py && \
    /opt/flossware/venv/bin/python /opt/flossware/coding-agent-setup/scripts/setup.py --help >/dev/null && \
    /opt/flossware/venv/bin/pa --help >/dev/null

RUN cat > /usr/local/bin/flossware-setup <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec /opt/flossware/venv/bin/python /opt/flossware/coding-agent-setup/scripts/setup.py "$@"
EOF
RUN chmod 755 /usr/local/bin/flossware-setup

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/flossware-setup"]
