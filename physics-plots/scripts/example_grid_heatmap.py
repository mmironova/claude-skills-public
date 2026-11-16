#!/usr/bin/env python3
"""Worked example and smoke test for plotstyle.grid_heatmap and save_linlog: a mass x lifetime map with a value,
an error and a low-statistics marker in each cell, one missing (white) cell, and a lin/log distribution overlay.

usage: example_grid_heatmap.py [out_dir]     (default: current directory)
Uses made-up numbers; it shows the layout, not physics.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plotstyle as ps  # noqa: E402

MASSES = ["0.4", "0.9", "1.8", "4.5", "10"]
CTAUS = ["0.1", "1", "5", "20"]


def main(out):
    random.seed(1)
    cells = {}
    for i in range(len(MASSES)):
        for j in range(len(CTAUS)):
            if (i, j) == (4, 3):
                continue                                   # missing sample -> white cell
            v = 2.0 + 1.5 * i - 0.8 * j + random.uniform(-0.5, 0.5)
            n = 30 if j == 3 else 400
            lines = [f"{v:.1f}%{'*' if n < 50 else ''}", f"#pm{0.1 * v + 0.2:.1f}"]
            cells[(i, j)] = {"value": v, "lines": lines}
    ps.grid_heatmap("example_map", MASSES, CTAUS, cells,
                    ["Signal model X, signal region A, #sqrt{s} = 13.6 TeV",
                     "Relative change in signal efficiency",
                     "Cell: #delta #pm stat. * N < 50; white: no sample"],
                    "#delta [%]", 0, 8, f"{out}/example_grid_heatmap")

    c = ps.canvas("example_dist")
    a = ps.th1("a", (40, 0, 4), [random.gauss(1.5, 0.5) for _ in range(5000)], ps.bright("blue"), norm=True,
               xtitle="m_{X} [GeV]", ytitle="Fraction of events / 0.1 GeV")
    b = ps.th1("b", (40, 0, 4), [random.gauss(1.8, 0.7) for _ in range(5000)], ps.bright("red"), norm=True, style=2)
    a.Draw("HIST E"); b.Draw("HIST E SAME")
    y = ps.atlas_label(["#sqrt{s} = 13.6 TeV", "Simulation, made-up numbers"])
    leg = ps.legend(0.62, 0.80, 0.92, 0.91, size=0.035)
    leg.AddEntry(a, "Model A", "l"); leg.AddEntry(b, "Model B", "l"); leg.Draw()
    ps.save_linlog(c, [a, b], f"{out}/example_distribution")
    print("label bottom at NDC y =", round(y, 2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
