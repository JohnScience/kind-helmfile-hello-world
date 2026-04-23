#!/usr/bin/env python3
"""Build the hello-world Docker image."""

import os
import re
import subprocess
import sys
import urllib.request


def latest_rust_version() -> str:
    url = "https://static.rust-lang.org/dist/channel-rust-stable.toml"
    print("Fetching latest stable Rust version...")
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:  # noqa: S310
            content = resp.read().decode()
    except Exception as exc:
        print(f"Failed to fetch Rust version ({exc}), falling back to 1.85", file=sys.stderr)
        return "1.85"
    # The TOML file contains:  version = "1.XX.Y (hash date)"  under [pkg.rust]
    match = re.search(r'^\[pkg\.rust\].*?^version\s*=\s*"(\d+\.\d+)\.\d+', content, re.M | re.S)
    if not match:
        print("Could not parse Rust version from release channel, falling back to 1.85", file=sys.stderr)
        return "1.85"
    version = match.group(1)
    print(f"Latest stable Rust: {version}")
    return version


IMAGE_NAME = os.environ.get("IMAGE_NAME", "hello-world")
IMAGE_TAG = os.environ.get("IMAGE_TAG", "latest")
full_image = f"{IMAGE_NAME}:{IMAGE_TAG}"
rust_version = latest_rust_version()

print(f"Building Docker image: {full_image}")

result = subprocess.run(
    [
        "docker", "build",
        "-f", "hello-world.dockerfile",
        "--build-arg", f"RUST_VERSION={rust_version}",
        "-t", full_image,
        ".",
    ],
    check=False,
)

if result.returncode != 0:
    print(f"Docker build failed with exit code {result.returncode}", file=sys.stderr)
    sys.exit(result.returncode)

print(f"Build complete: {full_image}")
