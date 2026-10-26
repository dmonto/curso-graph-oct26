#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python --version
