#!/usr/bin/env python3
"""Deploy the hello-world helmfile application to a local kind cluster."""

import os
import platform
import shutil
import subprocess
import sys

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

IMAGE_NAME   = os.environ.get("IMAGE_NAME",   "hello-world")
IMAGE_TAG    = os.environ.get("IMAGE_TAG",    "latest")
KIND_CLUSTER = os.environ.get("KIND_CLUSTER", "kind")

_OS         = platform.system()  # "Windows", "Darwin", "Linux"
_FULL_IMAGE = f"{IMAGE_NAME}:{IMAGE_TAG}"

# ---------------------------------------------------------------------------
# Required tools and install hints per platform
# ---------------------------------------------------------------------------

_INSTALL_HINTS: dict[str, dict[str, str]] = {
    "kind": {
        "Windows": "scoop install kind  (or: winget install Kubernetes.kind)",
        "Darwin":  "brew install kind",
        "Linux":   "https://kind.sigs.k8s.io/docs/user/quick-start/#installation",
    },
    "helm": {
        "Windows": "scoop install helm  (or: winget install Helm.Helm)",
        "Darwin":  "brew install helm",
        "Linux":   "https://helm.sh/docs/intro/install/",
    },
    "helmfile": {
        "Windows": "scoop install helmfile  (or: mise use -g helmfile@latest)",
        "Darwin":  "brew install helmfile  (or: mise use -g helmfile@latest)",
        "Linux":   "mise use -g helmfile@latest  (or: pacman -S helmfile on Arch)",
    },
    # helm-diff's install script requires PowerShell Core on Windows
    "pwsh": {
        "Windows": "winget install Microsoft.PowerShell",
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hint(tool: str) -> str:
    return _INSTALL_HINTS.get(tool, {}).get(_OS, f"please install '{tool}' manually")


def require_binary(name: str) -> None:
    """Exit with a clear message if a CLI binary is not on PATH."""
    if shutil.which(name) is None:
        print(
            f"Error: '{name}' not found on PATH.\n"
            f"Install it: {_hint(name)}",
            file=sys.stderr,
        )
        sys.exit(1)


def require_helm_plugin(plugin_name: str, install_url: str) -> None:
    """Exit with a clear message if a helm plugin is not installed or not functional."""
    # Check presence in plugin list
    list_result = subprocess.run(
        ["helm", "plugin", "list"],
        check=False, capture_output=True, text=True,
    )
    installed = {
        line.split("\t")[0].strip()
        for line in list_result.stdout.splitlines()[1:]
        if line.strip()
    }
    if plugin_name not in installed:
        print(
            f"Error: helm plugin '{plugin_name}' is not installed.\n"
            f"Install it: helm plugin install {install_url}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Verify the plugin binary actually works (catches broken installs on Windows)
    probe = subprocess.run(
        ["helm", plugin_name, "version"],
        check=False, capture_output=True, text=True,
    )
    if probe.returncode != 0:
        print(
            f"Error: helm plugin '{plugin_name}' is listed but not functional.\n"
            f"Try reinstalling it:\n"
            f"  helm plugin uninstall {plugin_name}\n"
            f"  helm plugin install {install_url}",
            file=sys.stderr,
        )
        sys.exit(1)


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(
            f"Command {cmd[0]!r} failed with exit code {result.returncode}",
            file=sys.stderr,
        )
        sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------

require_binary("kind")
require_binary("helm")
require_binary("helmfile")
# helm-diff's install script uses pwsh (PowerShell Core) on Windows
if _OS == "Windows":
    require_binary("pwsh")
require_helm_plugin("diff", "https://github.com/databus23/helm-diff")

# ---------------------------------------------------------------------------
# Ensure kind cluster exists
# ---------------------------------------------------------------------------

existing = subprocess.run(
    ["kind", "get", "clusters"],
    check=False, capture_output=True, text=True,
)
if KIND_CLUSTER not in existing.stdout.splitlines():
    print(f"Creating kind cluster '{KIND_CLUSTER}'...")
    run(["kind", "create", "cluster", "--name", KIND_CLUSTER])
else:
    print(f"Kind cluster '{KIND_CLUSTER}' already exists.")

# ---------------------------------------------------------------------------
# Load image into cluster and deploy
# ---------------------------------------------------------------------------

print(f"Loading image {_FULL_IMAGE} into kind cluster '{KIND_CLUSTER}'...")
run(["kind", "load", "docker-image", _FULL_IMAGE, "--name", KIND_CLUSTER])

print("Deploying via helmfile...")
run(["helmfile", "apply"])

print("Deploy complete.")