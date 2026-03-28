# Nanobot Gateway Dockerfile
# Multi-stage build with uv
# Build context: ./nanobot with additional_contexts: workspace: .

ARG REGISTRY_PREFIX_DOCKER_HUB

# ---
# Stage 1: Build the application
# ---
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy root workspace files from workspace context
COPY --from=workspace pyproject.toml uv.lock ./

# Copy nanobot project files from build context
COPY pyproject.toml ./nanobot/
COPY entrypoint.py ./nanobot/

# Copy workspace members from workspace context
COPY --from=workspace mcp/mcp-lms ./mcp/mcp-lms/
COPY --from=workspace mcp/mcp-obs ./mcp/mcp-obs/
COPY --from=workspace nanobot-websocket-channel ./nanobot-websocket-channel/

# Sync dependencies from root workspace
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package nanobot

# ---
# Stage 2: Runtime image
# ---
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends gosu && rm -rf /var/lib/apt/lists/*

# Setup non-root user
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd --system --gid ${APP_GID} appgroup \
    && useradd --system --gid ${APP_GID} --uid ${APP_UID} --create-home appuser

# Copy application from builder
COPY --from=builder --chown=appuser:appgroup /app /app

# Set PATH to include venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app/nanobot

# Create writable workspace directory and config directory
RUN mkdir -p /app/nanobot/workspace /app/nanobot/config && chown appuser:appgroup /app/nanobot/workspace /app/nanobot/config

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:18790/health')" || exit 1

ENTRYPOINT ["python", "/app/nanobot/entrypoint.py"]
