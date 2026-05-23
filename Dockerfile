# syntax=docker/dockerfile:1.7

# --- dmm-builder: compile dmm-tools from source (no ARM prebuilt exists upstream) ---
FROM rust:1-slim-bookworm AS dmm-builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    git pkg-config libssl-dev && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch suite-1.10 https://github.com/SpaceManiac/SpacemanDMM /src \
    && cd /src \
    && cargo build --release --bin dmm-tools \
    && strip /src/target/release/dmm-tools


FROM python:3.12-slim AS builder
ARG VG13_SHA
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates ripgrep && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.5.4

COPY --from=dmm-builder /src/target/release/dmm-tools /usr/local/bin/dmm-tools

WORKDIR /build
COPY pyproject.toml uv.lock ./
COPY src/ src/
COPY pipeline/ pipeline/
RUN uv sync --no-dev

COPY pipeline/clone_vg13.sh .
RUN ./clone_vg13.sh "$VG13_SHA" /vg13

RUN uv run python -m pipeline.build_dm_index /vg13 /snapshot_intermediate/index

RUN uv run python -m pipeline.crawl_wiki /snapshot_intermediate/wiki

RUN uv run python -m pipeline.pack_artifacts /vg13 \
    /snapshot_intermediate/index /snapshot_intermediate/wiki \
    /snapshot "$VG13_SHA"


FROM python:3.12-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    ripgrep ca-certificates && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.5.4
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src/ src/
RUN uv sync --no-dev

COPY --from=builder /snapshot /snapshot
RUN mkdir -p /var/cache/vgstation13-mcp && chown -R app:app /var/cache/vgstation13-mcp

USER app
ENV VG_SNAPSHOT_DIR=/snapshot
ENV VG_CACHE_DIR=/var/cache/vgstation13-mcp
ENV VG_TRANSPORT=http
ENV PORT=8080
EXPOSE 8080
CMD ["uv", "run", "vgstation13-mcp"]
