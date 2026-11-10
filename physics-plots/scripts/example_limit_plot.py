#!/usr/bin/env python3
"""Worked example and smoke test for plotstyle.py: a limit-vs-mass plot with Brazil bands, two single-channel
curves, masked windows drawn first, a regime boundary, custom log-x labels and the save route.

usage: example_limit_plot.py [out_stem]     (default: ./example_limit_plot -> .pdf + .png)
Uses made-up numbers; it shows the layout, not physics.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plotstyle as ps  # noqa: E402

WINDOWS = [(0.7, 1.1), (2.8, 4.0)]      # mass regions masked out, e.g. around a resonance
BOUNDARY = 5.5                           # where the method changes


def fake(m, scale):
    return scale * 1e-4 * (1 + 0.6 * math.sin(3 * m)) * (m / 2) ** 0.4


def main(stem):
    ms = [0.4 + 0.05 * i for i in range(193)]
    exp = [fake(m, 1.0) for m in ms]
    obs = [e * (1 + 0.3 * math.sin(11 * m)) for m, e in zip(ms, exp)]
    chan_a = [fake(m, 1.6) for m in ms]
    chan_b = [fake(m, 2.2) for m in ms]

    c = ps.canvas("example", logx=True, logy=True)
    ymin = 2e-5
    ymax = ps.log_headroom(ymin, max(obs + chan_a + chan_b), frac=0.45)
    fr = ps.frame(0.4, 10, ymin, ymax, "m_{X} [GeV]", "95% CL upper limit on #sigma #times #it{B} [fb]")
    ps.log_x_labels(fr, [0.4, 0.5, 1, 2, 3, 5, 10], ymin)
    ps.boxes(WINDOWS, ymin, ymax / 30)                       # first: everything else draws over the windows
    first = {}
    for run in ps.segments(list(zip(ms, exp, obs, chan_a, chan_b)), breaks=(BOUNDARY,)):
        x = [p[0] for p in run]
        first.setdefault("b2", ps.band(x, [p[1] * 0.5 for p in run], [p[1] * 2.0 for p in run], ps.BAND2))
        first.setdefault("b1", ps.band(x, [p[1] * 0.7 for p in run], [p[1] * 1.4 for p in run], ps.BAND1))
        first.setdefault("a", ps.line(x, [p[3] for p in run], ps.palette(1), style=2, width=1))
        first.setdefault("b", ps.line(x, [p[4] for p in run], ps.palette(3), style=2, width=1))
        first.setdefault("exp", ps.line(x, [p[1] for p in run], 1, style=2))
        first.setdefault("obs", ps.line(x, [p[2] for p in run], 1))
    ps.vline(BOUNDARY, ymin, ymax / 30, style=3)
    leg = ps.legend(0.57, 0.66, 0.93, 0.92, size=0.033)
    leg.AddEntry(first["obs"], "Observed, combined", "l")
    leg.AddEntry(first["exp"], "Expected, combined", "l")
    leg.AddEntry(first["b1"], "Expected #pm 1#sigma", "f")
    leg.AddEntry(first["b2"], "Expected #pm 2#sigma", "f")
    leg.AddEntry(first["a"], "Expected, channel A", "l")
    leg.AddEntry(first["b"], "Expected, channel B", "l")
    leg.Draw()
    ps.atlas_label(["#sqrt{s} = 13 TeV, 140 fb^{-1}", "pp #rightarrow X + Y", "c#tau_{X} = 1 mm"])
    ps.save(c, stem)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "example_limit_plot")
