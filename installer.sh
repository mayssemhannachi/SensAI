#!/usr/bin/env bash
# SensAI - installation (une seule fois)
cd "$(dirname "$0")"
exec python3 scripts/installer.py "$@"
