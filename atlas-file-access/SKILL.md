---
name: atlas-file-access
description: How to find, check, download and read ATLAS data/MC files (AOD, DAOD_LLP1, DAOD_PHYS, analysis ntuples) on NERSC Perlmutter — rucio inside the ATLAS grid container, disk-vs-tape checks, PFNs and remote reads, downloads when sites refuse remote access, running AnalysisBase/xAOD pyROOT in shifter, and scanning many files in parallel on a compute node. Use this whenever the user wants to look at, rerun on, download, count events or objects in, or check the availability of ATLAS files or datasets, asks for rucio commands or a grid proxy, or needs information the ntuples don't carry (track links, decorations, vertex track weights), even if they don't mention rucio, xAOD or shifter.
---

# ATLAS file access on NERSC Perlmutter

`setupATLAS` does not work in a non-interactive shell here, the host is SUSE (no EL9 libraries), and the LCG view
has no xAOD dictionaries. So split the work by tool:

| Need | Where it runs |
|---|---|
| uproot / awkward / plain pyROOT on flat ntuples | LCG_106 view on the host (`scripts/lcg_python.sh script.py`) |
| rucio (list, replicas, rules, download) | ATLAS grid image via shifter (`scripts/in_grid_image.sh rucio ...`) |
| xAOD containers, decorations, CP tools | AnalysisBase inside the grid image (`scripts/in_analysisbase.sh script.py`) |

The scripts live next to this file in `scripts/`. They are small and readable; open them if a step fails.

Never mix uproot (LCG) and xAOD (AnalysisBase) in one process: their libraries clash. If a job needs both, extract
what you need from the ntuple into a pickle with LCG first, then read the pickle inside the AnalysisBase job.
The `env -i` in `in_analysisbase.sh` is there for the same reason — an inherited LCG environment breaks libstdc++.

## 1. Grid proxy

rucio reads `X509_USER_PROXY=/tmp/x509up_u$(id -u)`. `/tmp` is local to each login node: a proxy made on login40 is
invisible on login29. If rucio reports a missing or expired proxy, ask the user to run `voms-proxy-init -voms atlas`
on the current node — you cannot do it for them. Check the lifetime with `voms-proxy-info -timeleft` before long
downloads.

Compute nodes (salloc/srun) don't see the login node's `/tmp` either, so anything that needs the proxy (rucio,
remote `root://` reads) fails there with "Failed to open file". Split jobs: do the proxy-free heavy work (local files)
on the compute node, and the remote reads or rucio calls on the login node. Don't copy the proxy onto shared disk.

## 2. Finding datasets and checking availability

```bash
scripts/in_grid_image.sh rucio list-dids --filter type=CONTAINER 'data22_13p6TeV:data22_13p6TeV.00438364.physics_Main.deriv.DAOD_LLP1.*'
scripts/in_grid_image.sh rucio list-dataset-replicas <scope>:<dataset>      # RSEs holding complete copies
scripts/in_grid_image.sh rucio list-files <scope>:<dataset> --csv           # file names, sizes, events
scripts/in_grid_image.sh rucio list-rules --account $USER                   # your replication rules and their state
```

- DAOD → parent AOD: drop the `deriv.DAOD_X` part and the last p-tag, keep e/s/a/r tags; `recon.AOD.<tags>` containers
  resolve to `merge.AOD` datasets.
- A copy only on an RSE ending in `TAPE` needs a restore: a rucio rule to a DATADISK/LOCALGROUPDISK (or an R2D2
  request). Rules can sit for days on some tape sites; report which samples are blocked and where.
- When asked for a whole grid of samples, produce a table (sample × campaign → disk / tape / missing) and save it.

## 3. Reading files

- **Remote read**: get PFNs with `rucio list-file-replicas --pfns --protocols root <did>` and open them with
  `ROOT.TFile.Open("root://...")`. Don't use uproot's XRootD for this (fails with `readv_iov_max`).
- **Site refuses remote reads** (`[3010] Restriction FullyRestricted denied access for [READ_DATA]`): download instead.
  ```bash
  scripts/in_grid_image.sh rucio download --no-subdir --ndownloader 8 <scope>:<file1> <scope>:<file2> ...
  ```
  A DAOD_LLP1 file is ~1 GB; 8 threads give ~3–4 files/min. Some files fail on the first try — rerun with what did not
  land: `comm -23 <(sort wanted.txt) <(ls | grep pool.root | sort)`.
- Tell the user the disk footprint before a large download, and offer to delete the raw files once the per-file
  outputs exist.
- Shared CFS slows to a crawl while many downloads write to it; even `ls` can hang. Check progress from the rucio log
  (`grep -c "successfully downloaded"`), wrap checks in `timeout`, and don't poll.
- uproot cannot read non-split static aux stores (vertex positions, `trackParticleLinks`, muon track links): use xAOD.

## 4. xAOD pyROOT patterns (AnalysisBase 25.2.x)

```python
import ROOT; ROOT.gROOT.SetBatch(True); ROOT.xAOD.Init().ignore()
f = ROOT.TFile.Open(fn); t = ROOT.xAOD.MakeTransientTree(f)
for i in range(t.GetEntries()):
    t.GetEntry(i)
    mus = t.Muons                      # containers are attributes
    m = mus.at(0)                      # use .at(i), not [i]
    tp = m.trackParticle(ROOT.xAOD.Muon.InnerDetectorTrackParticle)
ROOT.xAOD.ClearTransientTrees(); f.Close()
```

- A missing attribute (`'xAODTEventTree' object has no attribute 'X'`) usually means the container is not in that
  derivation version. Check `f.Get("CollectionTree").GetListOfBranches()` and compare p-tags before debugging code.
- `TEvent.retrieve` templating fails from python; use the transient tree.
- Decorations: `acc = ROOT.SG.ConstAccessor('float')("name")`, test `acc.isAvailable(obj)` before `acc(obj)`.
- Hit summaries: `v = ctypes.c_uint8(0); tp.summaryValue(v, ROOT.xAOD.numberOfSCTHits)` (not `ROOT.uint8_t`).
- Same object across containers: compare `ROOT.addressof(a) == ROOT.addressof(b)`, not python `id()`.
- Container of an ElementLink: `link.dataID()`.
- CP tools are configured with `setProperty(...)` then `initialize()`; call `.ignore()` on returned StatusCodes or check
  them explicitly when debugging.

## 5. Many files: per-file scans on a compute node

Write the scan to take `out.pkl file1 [file2 ...]` and dump a dict of numpy arrays. One pickle per input file makes
reruns skip finished files and makes merging trivial. Then run on one interactive CPU node:

```bash
scripts/scan_on_node.sh list_of_files.txt /path/to/scan.py /path/to/outdir 64
```

It allocates one node (`salloc -A $NERSC_ACCOUNT -q interactive -C cpu -N 1`, account `atlas` by default), runs the scan in AnalysisBase with 64 files in
parallel, skips files whose output exists, and writes one log per file. Afterwards `grep -l Traceback outdir/*.log`
lists failures. Launch long downloads and scans in the background and report from logs.

## 6. Before reporting

State the dataset names, derivation tags, number of files/events used out of the total, and anything excluded.
If only part of a run or sample was processed, say so and give the fraction.
