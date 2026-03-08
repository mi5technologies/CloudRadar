#!/bin/bash
set -e
cd "$(dirname "$0")/.."
python -m cspm.cli ui --host 127.0.0.1 --port 8000

