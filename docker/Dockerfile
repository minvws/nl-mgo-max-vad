# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.11

###########################################################
# Base image with system deps
###########################################################
FROM python:${PYTHON_VERSION}-bookworm AS base

ARG PROJECT_DIR="/src" \
    LOCAL_SOURCE_DIR="." \
    NODE_VERSION=22 \
    APP_USER="app" \
    APP_GROUP="app" \
    NEW_UID=1000 \
    NEW_GID=1000 \
    INSTALL_NPM_ASSETS=true \
    XMLSEC_VERSION=1.3.15 \
    LXML_VERSION=5.4.0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry-cache \
    WHEELHOUSE=/wheels

# Create non-privileged user
RUN groupadd --system ${APP_GROUP} --gid=${NEW_GID} && \
    adduser \
    --disabled-password \
    --gecos "" \
    --uid ${NEW_UID} \
    --gid ${NEW_GID} \
    ${APP_USER}

RUN apt update && \
    apt install -y \
    curl \
    iputils-ping \
    git \
    gnupg2 \
    libxmlsec1-dev \
    pkg-config \
    lsb-release \
    make \
    openssh-client  \
    && curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

RUN pip3 install --upgrade pip && \
    pip3 install poetry --no-cache-dir

###########################################################
# Wheels stage: build heavy packages from source
###########################################################
FROM base AS wheels

RUN mkdir -p ${WHEELHOUSE}

# Build wheels from source
RUN pip wheel --no-binary xmlsec,lxml --wheel-dir=${WHEELHOUSE} xmlsec==${XMLSEC_VERSION} lxml==${LXML_VERSION}

###########################################################
# Builder stage: package installations with poetry and npm
###########################################################
FROM base AS builder

# Copy prebuilt wheels
COPY --from=wheels ${WHEELHOUSE} ${WHEELHOUSE}

# Faster installation of heavy packages from wheelhouse
RUN pip install --no-cache-dir --no-index --find-links=${WHEELHOUSE} --only-binary=:all: xmlsec==${XMLSEC_VERSION} lxml==${LXML_VERSION}

WORKDIR ${PROJECT_DIR}

COPY local-packages ./local-packages
COPY pyproject.toml poetry.lock poetry.toml ./

# Setup SSH known_hosts for builder
RUN mkdir -p ~/.ssh && \
    ssh-keyscan -H github.com >> ~/.ssh/known_hosts

# Install python packages
RUN --mount=type=ssh \
    --mount=type=cache,target=${POETRY_CACHE_DIR} \
    --mount=type=secret,id=github_token,required=false \
    if [ -s /run/secrets/github_token ]; then \
        GITHUB_TOKEN=$(cat /run/secrets/github_token); \
        git config --global url."https://${GITHUB_TOKEN}@github.com/".insteadOf "git@github.com:"; \
        git config --global url."https://${GITHUB_TOKEN}@github.com/".insteadOf "ssh://git@github.com/"; \
    fi; \
    poetry install --no-interaction; \
    if [ -s /run/secrets/github_token ]; then rm -f /root/.gitconfig; fi

# Install npm packages
RUN mkdir -p node_modules static/assets
COPY scripts/setup-npm.sh vite.config.js package.json package-lock.json ./
COPY resources ./resources

RUN --mount=type=secret,id=npmrc,target=${PROJECT_DIR}/.npmrc \
    if [ "$INSTALL_NPM_ASSETS" = "true" ]; then \
        chmod +x setup-npm.sh && ./setup-npm.sh; \
        npm run build; \
    fi

###########################################################
# Final runtime stage
###########################################################
FROM base

ARG PYTHON_VERSION

# Copy built site-packages and binaries
COPY --chown=${APP_USER}:${APP_GROUP} --from=builder /usr/local /usr/local
RUN chown -R ${APP_USER}:${APP_GROUP} /usr/local/lib/python${PYTHON_VERSION}/site-packages

# Copy app source code
COPY --chown=${APP_USER}:${APP_GROUP} ${LOCAL_SOURCE_DIR}/ ${PROJECT_DIR}

# Copy built npm assets
COPY --from=builder --chown=${APP_USER}:${APP_GROUP} ${PROJECT_DIR}/node_modules ${PROJECT_DIR}/node_modules
COPY --from=builder --chown=${APP_USER}:${APP_GROUP} ${PROJECT_DIR}/static/assets ${PROJECT_DIR}/static/assets

ENV PATH="/usr/local/bin:$PATH"
ENV PYTHONPATH=${PROJECT_DIR}

# Setup SSH known_hosts for runtime
RUN mkdir -p /home/${APP_USER}/.ssh && \
    ssh-keyscan -H github.com >> /home/${APP_USER}/.ssh/known_hosts && \
    chown -R ${APP_USER}:${APP_GROUP} /home/${APP_USER}/.ssh

WORKDIR ${PROJECT_DIR}
EXPOSE 8006

USER ${APP_USER}

CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5676", "-m", "app.main"]
