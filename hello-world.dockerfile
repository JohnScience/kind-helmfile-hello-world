# Build stage
ARG RUST_VERSION=1.85
FROM rust:${RUST_VERSION}-slim AS builder

WORKDIR /app
COPY rust/ .

RUN cargo build --release --package hello-world

# Runtime stage
FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/target/release/hello-world .

EXPOSE 8080

CMD ["./hello-world"]
