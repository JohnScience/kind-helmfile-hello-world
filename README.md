# kind-helmfile-hello-world

A minimal hello-world web server deployed to a local [kind](https://kind.sigs.k8s.io/) Kubernetes cluster using [Helmfile](https://helmfile.readthedocs.io/) for bootstrapping.

## Stack

- **Rust** — stdlib-only HTTP/1.1 server (no dependencies)
- **Docker** — multi-stage build; latest stable Rust fetched at build time
- **Helm** — local chart at `k8s/charts/hello-world/`
- **Helmfile** — single release declared in `helmfile.yaml`
- **kind** — local Kubernetes cluster
- **Python 3** — build and deploy scripts

## Prerequisites

| Tool | Install |
|------|---------|
| Docker | https://docs.docker.com/get-docker/ |
| kind | `scoop install kind` / `brew install kind` |
| kubectl | `scoop install kubectl` / `brew install kubectl` |
| helm | `scoop install helm` / `brew install helm` |
| helmfile | `scoop install helmfile` / `brew install helmfile` |
| Python 3.10+ | https://www.python.org/downloads/ |
| pwsh (Windows) | `winget install Microsoft.PowerShell` |

## Usage

### 1. Build the Docker image

```sh
python -m scripts.build
```

Fetches the latest stable Rust version, builds the image, and tags it as `hello-world:latest`.

### 2. Deploy to kind

```sh
python -m scripts.deploy            # dev (default)
python -m scripts.deploy --env prod # prod
```

This will:
1. Run preflight checks (required binaries and helm plugins)
2. Create a kind cluster named `kind` if one does not exist
3. Load the `hello-world:latest` image into the cluster
4. Run `helmfile -e <env> apply`

Each environment deploys into its own namespace (`dev` or `prod`).

### 3. Verify

Forward a local port to the service. Avoid port 8080 if Docker Desktop is running — it occupies that port.

```sh
kubectl port-forward -n dev svc/hello-world-hello-world 9090:80
```

Then in another terminal:

```sh
curl http://127.0.0.1:9090/
curl http://127.0.0.1:9090/health
```

Expected responses: `Hello, World!` and `ok`.

## Environments

| Environment | Namespace | Replicas | Pull policy |
|-------------|-----------|----------|-------------|
| `dev` | `dev` | 1 | `IfNotPresent` |
| `prod` | `prod` | 2 | `Always` |

Per-environment values live in `k8s/environments/<env>/values.yaml` and are merged on top of the base chart values.

## Project structure

```
.
├── hello-world.dockerfile      # Multi-stage Docker build
├── helmfile.yaml               # Helmfile environments + release definition
├── k8s/
│   ├── charts/
│   │   └── hello-world/        # Local Helm chart (base values)
│   └── environments/
│       ├── dev/values.yaml     # Dev overrides
│       └── prod/values.yaml    # Prod overrides
├── rust/
│   ├── Cargo.toml              # Workspace root
│   └── hello-world/
│       └── src/main.rs         # HTTP server
└── scripts/
    ├── build.py                # docker build wrapper
    └── deploy.py               # kind + helmfile deploy
```

## Endpoints

| Path | Status | Body |
|------|--------|------|
| `/` | 200 | `Hello, World!` |
| `/health` | 200 | `ok` |
| anything else | 404 | `not found` |

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IMAGE_NAME` | `hello-world` | Docker image name |
| `IMAGE_TAG` | `latest` | Docker image tag |
| `KIND_CLUSTER` | `kind` | kind cluster name |
