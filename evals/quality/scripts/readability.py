#!/usr/bin/env python3
"""Mechanical measures of a spec folder: length, reading time, sentence
measures, structure, repetition, and overlap with the brief. No model.

    python3 scripts/readability.py RUN_DIR
    python3 scripts/readability.py --spec SPEC_DIR [--brief BRIEF.md]

What these capture: how much there is to read and how it is laid out.
What they do not: whether any of it is correct, complete or useful.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import common as c  # noqa: E402

VAGUE = ["etc", "and so on", "as appropriate", "as needed", "if necessary", "where applicable",
         "should probably", "might want to", "somehow", "some kind of", "or similar", "and/or",
         "reasonable", "sensible", "appropriately", "properly", "gracefully", "robust",
         "user-friendly", "as required", "if possible", "where possible"]
PLACEHOLDER = re.compile(r"\b(TBD|TODO|TBC|FIXME|XXX)\b|\?\?\?|<[^<>\n]*fill[^<>\n]*>|lorem ipsum", re.I)
FENCE = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.S | re.M)


def syllables(word):
    word = word.lower()
    groups = re.findall(r"[aeiouy]+", word)
    n = len(groups)
    if word.endswith("e") and not word.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(n, 1)


def sentences_of(prose):
    out = []
    for line in prose.splitlines():
        line = line.strip()
        if not line or line.startswith("|") or re.match(r"^[-=*_]{3,}$", line):
            continue
        line = re.sub(r"^(#{1,6}\s+|[-*+]\s+(\[.\]\s+)?|\d+[.)]\s+|>\s*)", "", line)
        for part in re.split(r"(?<=[.!?])\s+", line):
            if re.search(r"[A-Za-z]{2}", part):
                out.append(part)
    return out


def shingles(text, n=5):
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def measure(spec_dir, brief_text=None):
    files = c.spec_files(spec_dir)
    text = c.spec_text(spec_dir)
    prose = FENCE.sub("\n", text)
    words = len(re.findall(r"\S+", text))
    prose_words = len(re.findall(r"\S+", prose))
    sents = sentences_of(prose)
    sent_lens = [len(s.split()) for s in sents]
    alpha = re.findall(r"[A-Za-z]+(?:'[a-z]+)?", " ".join(sents))
    lines = prose.splitlines()
    headings = [i for i, l in enumerate(lines) if re.match(r"^\s{0,3}#{1,6}\s+\S", l)]
    empty_sections = 0
    for pos, idx in enumerate(headings):
        end = headings[pos + 1] if pos + 1 < len(headings) else len(lines)
        level = len(re.match(r"^\s*(#+)", lines[idx]).group(1))
        body = [l for l in lines[idx + 1:end] if l.strip()]
        nxt_level = (len(re.match(r"^\s*(#+)", lines[end]).group(1)) if end < len(lines) else 0)
        if not body and nxt_level <= level:
            empty_sections += 1
    nonblank = [l for l in lines if l.strip()]
    seen, dup = set(), 0
    long_sents = [c.normalise(s) for s in sents if len(s.split()) >= 6]
    for s in long_sents:
        if s in seen:
            dup += 1
        seen.add(s)
    low = " " + c.normalise(prose) + " "
    vague = sum(len(re.findall(r"(?<![a-z])%s(?![a-z])" % re.escape(v), low)) for v in VAGUE)

    def ratio(a, b, digits=3):
        return round(a / b, digits) if b else None

    out = {
        "files": files,
        "file_count": len(files),
        "words": words,
        "prose_words": prose_words,
        "code_block_words": words - prose_words,
        "reading_minutes": ratio(words, c.READING_WPM, 2),
        "sentences": len(sents),
        "avg_sentence_words": ratio(sum(sent_lens), len(sents), 1),
        "long_sentence_share": ratio(sum(n > 30 for n in sent_lens), len(sents)),
        "flesch_reading_ease": (round(206.835 - 1.015 * len(alpha) / len(sents)
                                      - 84.6 * sum(map(syllables, alpha)) / len(alpha), 1)
                                if sents and alpha else None),
        "headings": len(headings),
        "words_per_heading": ratio(words, len(headings), 0),
        "empty_sections": empty_sections,
        "list_line_share": ratio(sum(bool(re.match(r"^\s*([-*+]|\d+[.)])\s", l)) for l in nonblank),
                                 len(nonblank)),
        "table_lines": sum(l.strip().startswith("|") for l in nonblank),
        "duplicate_sentence_share": ratio(dup, len(long_sents)),
        "vague_terms_per_1000_words": ratio(vague * 1000, prose_words, 1),
        "placeholders": len(PLACEHOLDER.findall(text)),
    }
    if brief_text is not None:
        spec_sh, brief_sh = shingles(text), shingles(brief_text)
        brief_words = len(re.findall(r"\S+", brief_text))
        out.update({
            "brief_words": brief_words,
            "length_ratio_to_brief": ratio(words, brief_words, 2),
            # share of the spec's 5-word runs that are copied from the brief
            "copied_from_brief_share": ratio(len(spec_sh & brief_sh), len(spec_sh)),
            # share of the brief's 5-word runs that reappear in the spec
            "brief_reused_share": ratio(len(spec_sh & brief_sh), len(brief_sh)),
        })
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", nargs="?")
    ap.add_argument("--spec")
    ap.add_argument("--brief")
    args = ap.parse_args(argv)
    if args.run_dir:
        meta = c.run_meta(args.run_dir)
        brief = c.read_text(os.path.join(c.problem_dir(meta["problem"]), "brief.md"))
        result = measure(c.frozen_spec(args.run_dir), brief)
        c.dump_json(os.path.join(args.run_dir, "scores", "readability.json"), result)
    elif args.spec:
        result = measure(args.spec, c.read_text(args.brief) if args.brief else None)
    else:
        ap.error("give RUN_DIR or --spec")
    import json
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
