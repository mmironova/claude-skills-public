#!/bin/bash
# Run a per-file xAOD scan over many files on one interactive CPU node.
# Usage: scan_on_node.sh FILELIST SCAN_SCRIPT OUTDIR [NPARALLEL=64] [HOURS=2]
# The NERSC allocation is $NERSC_ACCOUNT (default: atlas).
# SCAN_SCRIPT is called as: python3 SCAN_SCRIPT OUTDIR/<basename>.pkl <file>; files with an existing pkl are skipped.
HERE=$(cd "$(dirname "$0")" && pwd)
L=$(readlink -f "$1"); SCAN=$(readlink -f "$2"); OUT=$(readlink -f "$3"); NP=${4:-64}; HRS=${5:-2}
mkdir -p "$OUT"
salloc -A ${NERSC_ACCOUNT:-atlas} -q interactive -C cpu -N 1 -t 0${HRS}:00:00 --image=docker:atlasadc/atlas-grid-almalinux9:latest --module=cvmfs \
  srun -n 1 -c 256 shifter bash -c "cat $L | xargs -P $NP -I{} bash -c 'b=\$(basename {}); b=\${b%.root*}; b=\${b%.pool}; \
    [ -s $OUT/\$b.pkl ] && exit 0; \
    env -i HOME=$HOME PATH=/usr/bin:/bin bash --noprofile --norc -c \"source $HERE/ab_env.sh >/dev/null 2>&1; python3 $SCAN $OUT/\$b.pkl {}\" > $OUT/\$b.log 2>&1'"
echo "outputs: $(ls $OUT/*.pkl 2>/dev/null | wc -l); failures: $(grep -l Traceback $OUT/*.log 2>/dev/null | wc -l)"
