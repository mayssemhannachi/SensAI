#!/usr/bin/env bash
# SensAI - demarrage de la plateforme
cd "$(dirname "$0")"
exec python3 scripts/demarrer.py "$@"
