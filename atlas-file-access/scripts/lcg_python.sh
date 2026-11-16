#!/bin/bash
# Run a python script with the LCG_106 view (ROOT 6.32, uproot, awkward, numpy, scipy). Usage: lcg_python.sh script.py [args]
source /cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-opt/setup.sh >/dev/null 2>&1
exec /cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-opt/bin/python3 "$@"
