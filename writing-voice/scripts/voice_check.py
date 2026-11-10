#!/usr/bin/env python3
"""Sentence statistics and voice flags for a .tex, .md or .txt draft.

    python3 voice_check.py draft.tex [--rules rules.json] [--max-words 30] [--quiet]

Strips LaTeX comments, math, figure/table/equation environments and commands, splits the
prose into sentences, and reports

  - sentence count, median / 90th percentile / maximum length,
  - sentences above --max-words and suspiciously short ones,
  - a choppiness measure (share of sentences under ten words, longest run of them),
  - every pattern the rules file says this author does not use,

each with its line number. The exit code is always 0; this is a linter, not a judge.

The patterns are not built in. They come from a JSON rules file describing one author:
`rules.json` next to this script if it exists, otherwise `rules.example.json`, otherwise
a minimal default. See rules.example.json for the format and writing-voice/SKILL.md for
how to build one from a corpus.
"""
import argparse
import json
import re
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent

DEFAULT_RULES = {
    "max_words": 30,
    "short_words": 10,
    "rhetoric": [],
    "fragment_starts": [],
    "spelling": [],
    "naming": [],
    "flag_dashes": True,
    "flag_semicolons": False,
    "flag_x_not_y": False,
    "flag_questions": False,
    "flag_placeholders": True,
    "target": {},
}


def load_rules(path=None):
    for cand in ([Path(path)] if path else [HERE / "rules.json", HERE / "rules.example.json"]):
        if cand.exists():
            rules = dict(DEFAULT_RULES)
            rules.update(json.loads(cand.read_text(encoding="utf-8")))
            rules["_source"] = str(cand)
            return rules
    return dict(DEFAULT_RULES, _source="built-in defaults")


def strip_latex(text):
    text = re.sub(r"(?<!\\)%.*", "", text)
    text = re.sub(r"\\begin\{(figure|table|equation|align|tabular|tabularx)\*?\}.*?"
                  r"\\end\{\1\*?\}", " ", text, flags=re.S)
    text = re.sub(r"\$\$.*?\$\$|\\\[.*?\\\]|\$[^$]*\$", " QTY ", text, flags=re.S)
    text = re.sub(r"\\(?:SI|SIrange|num|ang)\s*(\[[^\]]*\])?(\{[^{}]*\}){1,3}", "QTY", text)
    text = re.sub(r"\\(?:cite|ref|label|eqref|url|href|includegraphics)\s*(\[[^\]]*\])?\{[^}]*\}", "", text)
    text = re.sub(r"\\(?:section|subsection|subsubsection|chapter|title)\*?\{[^{}]*\}", " . ", text)
    text = re.sub(r"\\caption\{", " . ", text)
    text = re.sub(r"\\(?:begin|end)\{[^{}]*\}", " ", text)
    text = re.sub(r"\\[a-zA-Z]+\*?", " ", text)
    text = re.sub(r"[{}~]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def sentences_with_lines(raw):
    """Yield (line_no, sentence, n_words) over the stripped prose."""
    marked = "\n".join(f"\x00{i}\x00{l}" for i, l in enumerate(raw.split("\n"), 1))
    text = strip_latex(marked)
    text = re.sub(r"\x00(\d+)\x00", lambda m: " \x00" + m.group(1) + "\x00 ", text)
    for ab in ("et al.", "e.g.", "i.e.", "vs.", "cf.", "Fig.", "Figs.", "Eq.", "Eqs.",
               "Sec.", "Ref.", "Refs.", "approx.", "resp.", "Dr.", "Prof.", "no.", "No."):
        text = text.replace(ab, ab[:-1])
    parts = re.split(r"(?<=[.!?])\s+(?=\S)", text)
    current_line = 1
    for p in parts:
        nums = re.findall(r"\x00(\d+)\x00", p)
        if nums:
            current_line = int(nums[0])
        s = re.sub(r"\x00\d+\x00", " ", p)
        s = re.sub(r"\s+", " ", s).strip(" .")
        words = [w for w in s.split() if re.search(r"[A-Za-z]", w)]
        if words:
            yield current_line, s, len(words)


def pattern_flags(raw, rules):
    """Line-by-line flags from the rules file."""
    out = []
    short_rhetoric = [(p, f"rhetorical word ({p.strip(chr(92) + 'b')})") for p in rules["rhetoric"]]
    spelling = [(p, f"spelling ({p.strip(chr(92) + 'b')})") if isinstance(p, str) else (p[0], p[1])
                for p in rules["spelling"]]
    naming = [(p[0], f"naming: {p[1]}") for p in rules["naming"]]
    for i, line in enumerate(raw.split("\n"), 1):
        plain = re.sub(r"(?<!\\)%.*", "", line)
        prose = strip_latex(plain)
        if rules["flag_dashes"] and ("\u2014" in plain or re.search(r"(?<!-)---(?!-)", plain) or " -- " in plain):
            out.append((i, "dash used as punctuation", plain.strip()))
        if rules["flag_semicolons"] and ";" in prose and not re.search(r"\\[a-z]+;", plain):
            out.append((i, "semicolon", plain.strip()))
        if rules["flag_x_not_y"] and re.search(r",\s*not\s+(?:a|an|the|of|in|by)?\s*\w+[.,]", prose):
            out.append((i, "'X, not Y' contrast", plain.strip()))
        if rules["flag_questions"] and re.search(r"\?(\s|$)", prose):
            out.append((i, "question in prose", plain.strip()))
        if rules["flag_placeholders"] and re.search(r"\\todo|\bTBD\b|\bTODO\b|to be added", plain):
            out.append((i, "placeholder left in draft", plain.strip()))
        for pat, why in short_rhetoric + spelling + naming:
            if re.search(pat, prose, re.I if (pat, why) in short_rhetoric else 0):
                out.append((i, why, plain.strip()))
        for pat in rules["fragment_starts"]:
            if re.search(pat, prose):
                out.append((i, "sentence starting with a fragment word", plain.strip()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--rules", help="JSON rules file (default: rules.json beside this script)")
    ap.add_argument("--max-words", type=int, default=None)
    ap.add_argument("--quiet", action="store_true", help="statistics only")
    a = ap.parse_args()
    rules = load_rules(a.rules)
    max_words = a.max_words or rules["max_words"]
    short_words = rules["short_words"]

    raw = Path(a.file).read_text(encoding="utf-8")
    sents = list(sentences_with_lines(raw))
    lens = sorted(n for _, _, n in sents if n >= 3)
    if not lens:
        print("no prose found")
        return
    p90 = lens[int(0.9 * (len(lens) - 1))]
    print(f"rules: {rules['_source']}")
    print(f"{len(lens)} sentences, median {statistics.median(lens):.0f} words, "
          f"90th percentile {p90}, longest {lens[-1]}")
    target = rules.get("target") or {}
    if target:
        print("  target for this author: " + ", ".join(f"{k} {v}" for k, v in target.items()))
    short_share = sum(1 for n in lens if n < short_words) / len(lens)
    run = best = 0
    for _, _, n in sents:
        run = run + 1 if n < short_words else 0
        best = max(best, run)
    print(f"choppiness: {100 * short_share:.0f} % of sentences under {short_words} words, "
          f"longest run of short sentences {best}"
          + ("  <- reads as a list, join sentences" if short_share > 0.15 or best >= 3 else ""))

    long_ = [(ln, s, n) for ln, s, n in sents if n > max_words]
    frags = [(ln, s, n) for ln, s, n in sents if n < 4 and not s.isupper()]
    flags = pattern_flags(raw, rules)
    if a.quiet:
        print(f"{len(long_)} long, {len(frags)} fragments, {len(flags)} pattern flags")
        return
    if long_:
        print(f"\nSentences above {max_words} words:")
        for ln, s, n in long_:
            print(f"  L{ln} ({n}): {s[:110]}{'...' if len(s) > 110 else ''}")
    if frags:
        print("\nVery short sentences (fragments?):")
        for ln, s, n in frags:
            print(f"  L{ln}: {s}")
    if flags:
        print("\nPattern flags:")
        for ln, why, s in flags:
            print(f"  L{ln} {why}: {s[:100]}{'...' if len(s) > 100 else ''}")
    if not (long_ or frags or flags):
        print("\nno flags")


if __name__ == "__main__":
    main()
