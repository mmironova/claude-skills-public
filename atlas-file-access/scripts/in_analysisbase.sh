#!/bin/bash
# Run a python script with AnalysisBase (xAOD, CP tools) inside the grid image, with a clean environment.
# Usage: in_analysisbase.sh script.py [args]      (inside an allocation: set INSIDE_SHIFTER=1 to skip the shifter call)
HERE=$(cd "$(dirname "$0")" && pwd)
ARGS=$(printf '%q ' "$@")
INNER="env -i HOME=$HOME PATH=/usr/bin:/bin bash --noprofile --norc -c \"source $HERE/ab_env.sh >/dev/null 2>&1; python3 $ARGS\""
if [ -n "$INSIDE_SHIFTER" ]; then eval "$INNER"; else
  exec shifter --image=docker:atlasadc/atlas-grid-almalinux9:latest --module=cvmfs bash -c "$INNER"; fi
