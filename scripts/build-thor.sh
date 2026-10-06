#!/bin/bash
# Builds Artemis for AYN Thor inside Podman container
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Building Artemis for AYN Thor (ARM64) ==="
cd "${ROOT_DIR}"

if ! podman image exists artemis-builder:latest; then
    echo "Building artemis-builder container..."
    podman build -t artemis-builder:latest -f "${SCRIPT_DIR}/Containerfile.thor" .
fi

echo "Running qmake6 inside container..."
podman run --rm -v "${ROOT_DIR}:/src:z" -w /src artemis-builder \
    qmake6 artemis.pro CONFIG+=release QMAKE_CXXFLAGS+=-fPIC

echo "Compiling Artemis..."
podman run --rm -v "${ROOT_DIR}:/src:z" -w /src artemis-builder \
    make -j"$(nproc)"

echo "Stripping binary..."
podman run --rm -v "${ROOT_DIR}:/src:z" -w /src artemis-builder \
    strip -o /src/app/artemis-stripped /src/app/artemis

echo "Build complete: app/artemis-stripped"
