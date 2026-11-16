#!/bin/bash
# Run a command (e.g. rucio, voms-proxy-info) inside the ATLAS grid image with rucio set up.
# Usage: in_grid_image.sh rucio list-files <did>
# The grid proxy must already exist at /tmp/x509up_u$(id -u) on THIS login node (voms-proxy-init -voms atlas).
CMD=$(printf '%q ' "$@")
exec shifter --image=docker:atlasadc/atlas-grid-almalinux9:latest --module=cvmfs bash -c "
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
export ALRB_noGridMW=NO
export RUCIO_ACCOUNT=\${RUCIO_ACCOUNT:-$USER}
export X509_USER_PROXY=/tmp/x509up_u\$(id -u)
source \${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh --quiet >/dev/null 2>&1
lsetup rucio --quiet >/dev/null 2>&1
$CMD"
