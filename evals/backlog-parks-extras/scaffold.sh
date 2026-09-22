#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"
"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block
