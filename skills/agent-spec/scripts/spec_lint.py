#!/usr/bin/env python3
"""Lint the structure, lengths, requirement patterns and glossary of a spec.

The rules are in references/rules.md. Vale checks the prose style rules;
run scripts/lint.sh to run both. Standard library only.

Usage: spec_lint.py SPEC.md [--glossary glossary.md] [--repo PATH] [--strict]
Exit code 1 when there are errors (or warnings, with --strict).
"""
import argparse
import re
import sys
from pathlib import Path

ORDER = ["Why", "Example", "Check", "Requirements", "Design", "Cases"]
OPTIONAL = {"Design"}
STATUSES = {"Draft", "In review", "Approved", "Implemented", "Superseded"}
FINAL = {"Approved", "Implemented"}
UNCHANGED = "Unchanged"

MODAL = r"(?:MUST NOT|MUST|SHOULD NOT|SHOULD|MAY)"
EARS = [re.compile(p) for p in (
    rf"^When .+, the .+? {MODAL} .+\.$",
    rf"^While .+, when .+, the .+? {MODAL} .+\.$",
    rf"^While .+, the .+? {MODAL} .+\.$",
    rf"^If .+, then the .+? {MODAL} .+\.$",
    rf"^(?:The|A|An) .+? {MODAL} .+\.$",
)]
OPEN = re.compile(r"\bOPEN\b")
OPEN_OK = re.compile(r"\bOPEN \([^)]+\): \S")
PATH = re.compile(r"`([\w.-]+(?:/[\w.-]+)+\.\w+)(?:::\w+)?`")

SENTENCE_MAX = 25
REQUIREMENT_MAX = 40
PARAGRAPH_MAX = 4
BULLET_MAX = 3
TABLE_ROWS_MAX = 8
WHY_MAX = 80
REQ_ROWS_WARN, REQ_ROWS_MAX = 15, 20
DOC_MAX = 1200


class Report:
    def __init__(self, path):
        self.path, self.errors, self.warnings = path, 0, 0

    def add(self, line, level, rule, message):
        if level == "E":
            self.errors += 1
        else:
            self.warnings += 1
        print(f"{self.path}:{line}: {level} {rule} {message}")


def clean(text):
    """Drop markup. A code span counts as one word."""
    text = re.sub(r"`[^`]*`", "CODE", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return text.replace("**", "").strip()


def sentences(text):
    text = clean(text)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text) if s.strip()]


def word_count(text):
    return sum(1 for t in clean(text).split() if re.search(r"[A-Za-z0-9]", t))


def split_row(line):
    cells, cell, in_code = [], "", False
    for ch in line.strip().strip("|"):
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            cells.append(cell.strip())
            cell = ""
        else:
            cell += ch
    cells.append(cell.strip())
    return cells


def parse(text):
    """Return ({section: [(kind, line, data)]}, [(section, line)]).

    Kinds: para, bullet, table, code, heading.
    """
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    sections, order = {"_head": []}, []
    current, para, para_line, in_code = "_head", [], 0, False

    def flush():
        nonlocal para
        if para:
            sections[current].append(("para", para_line, " ".join(para)))
            para = []

    for number, raw in enumerate(text.split("\n"), 1):
        line = raw.strip()
        if line.startswith("```"):
            flush()
            if not in_code:
                sections[current].append(("code", number, None))
            in_code = not in_code
        elif in_code:
            continue
        elif line.startswith("## "):
            flush()
            current = line[3:].strip()
            order.append((current, number))
            sections.setdefault(current, [])
        elif line.startswith("#"):
            flush()
            sections[current].append(("heading", number, line.lstrip("# ")))
        elif line.startswith("|"):
            flush()
            cells = split_row(line)
            if all(re.fullmatch(r":?-+:?", c) for c in cells):
                continue
            blocks = sections[current]
            if blocks and blocks[-1][0] == "table" and blocks[-1][2][-1][0] >= number - 2:
                blocks[-1][2].append((number, cells))
            else:
                blocks.append(("table", number, [(number, cells)]))
        elif re.match(r"(-|\d+\.)\s+", line):
            flush()
            sections[current].append(("bullet", number, re.sub(r"^(-|\d+\.)\s+", "", line)))
        elif not line:
            flush()
        else:
            if not para:
                para_line = number
            para.append(line)
    flush()
    return sections, order


def find_table(blocks, header):
    """Return (line of the first matching table, data rows of every matching table)."""
    first, out = None, []
    for kind, line, rows in blocks:
        if kind == "table" and [c.lower() for c in rows[0][1]] == [h.lower() for h in header]:
            first = first or line
            out.extend(rows[1:])
    return first, out


def load_glossary(path):
    banned = {}
    if not path or not Path(path).exists():
        return banned
    sections, _ = parse(Path(path).read_text())
    for blocks in sections.values():
        _, rows = find_table(blocks, ["Term", "Meaning", "Do not use"])
        for _, cells in rows:
            for word in cells[2].split(","):
                if word.strip():
                    banned[word.strip().lower()] = cells[0]
    return banned


def check_prose(rep, line, text, banned, limit=SENTENCE_MAX):
    for s in sentences(text):
        n = word_count(s)
        if n > limit:
            rep.add(line, "E", "L1", f"sentence has {n} words, maximum is {limit}: \"{s[:60]}...\"")
    plain = clean(text)
    for word, term in banned.items():
        if re.search(rf"\b{re.escape(word)}s?\b", plain, re.I):
            rep.add(line, "E", "G2", f"\"{word}\" is not a glossary term; use \"{term}\"")


def lint(path, glossary, repo):
    rep = Report(path)
    raw = Path(path).read_text()
    sections, order = parse(raw)
    banned = load_glossary(glossary)
    lines = {name: line for name, line in order}

    # S1 title and status line
    head = " ".join(str(d) for k, _, d in sections["_head"] if k == "para")
    if not re.match(r"# Spec: \S", raw.lstrip()):
        rep.add(1, "E", "S1", "first line must be \"# Spec: <title>\"")
    m = re.search(r"\*\*Status:\*\*\s*([^·]+)", head)
    status = m.group(1).strip() if m else None
    if status not in STATUSES:
        rep.add(3, "E", "S1", f"Status must be one of: {', '.join(sorted(STATUSES))}")
    for field in ("Decider", "Links"):
        if not re.search(rf"\*\*{field}:\*\*\s*\S", head):
            rep.add(3, "E", "S1", f"status line needs **{field}:**")

    # S2 sections
    names = [n for n, _ in order]
    for name in names:
        if name not in ORDER:
            rep.add(lines[name], "E", "S2", f"section \"{name}\" is not in the template")
    known = [n for n in names if n in ORDER]
    if known != [n for n in ORDER if n in known]:
        rep.add(1, "E", "S2", f"sections must be in this sequence: {', '.join(ORDER)}")
    for name in ORDER:
        if name not in names and name not in OPTIONAL:
            rep.add(1, "E", "S2", f"missing section \"{name}\"")

    # Prose rules and open items, on every section
    total = 0
    for name, blocks in sections.items():
        for kind, line, data in blocks:
            units = []
            if kind in ("para", "bullet"):
                units.append((line, data, SENTENCE_MAX))
                if kind == "para" and len(sentences(data)) > PARAGRAPH_MAX:
                    rep.add(line, "E", "L2", f"paragraph has more than {PARAGRAPH_MAX} sentences; split it or use a list")
                body = re.sub(r"^\*\*[^*]+\*\*\s*", "", data)
                if kind == "bullet" and len(sentences(body)) > BULLET_MAX:
                    rep.add(line, "E", "L2", f"bullet has more than {BULLET_MAX} sentences; split it")
            elif kind == "table":
                header = [c.lower() for c in data[0][1]]
                if len(data) - 1 > TABLE_ROWS_MAX:
                    rep.add(line, "E", "L6", f"table has {len(data) - 1} rows, maximum is {TABLE_ROWS_MAX}; split it under ### sub-headings")
                for rline, cells in data[1:]:
                    for column, cell in zip(header, cells):
                        limit = REQUIREMENT_MAX if column == "requirement" else SENTENCE_MAX
                        units.append((rline, cell, limit))
            for uline, text, limit in units:
                total += word_count(text)
                check_prose(rep, uline, text, banned, limit)
                if OPEN.search(text):
                    if not OPEN_OK.search(text):
                        rep.add(uline, "E", "S7", "write an open item as \"OPEN (owner): question\"")
                    if status in FINAL:
                        rep.add(uline, "E", "S7", f"a spec with Status {status} has no OPEN item")
    if total > DOC_MAX:
        rep.add(1, "E", "L4", f"spec has {total} words outside code blocks, maximum is {DOC_MAX}")

    # L3 Why
    if "Why" in sections:
        n = sum(word_count(d) for k, _, d in sections["Why"] if k in ("para", "bullet"))
        if n > WHY_MAX:
            rep.add(lines["Why"], "E", "L3", f"Why has {n} words, maximum is {WHY_MAX}")
        if n == 0:
            rep.add(lines["Why"], "E", "S2", "Why is empty")

    # S3 Requirements
    ids = []
    if "Requirements" in sections:
        blocks, sline = sections["Requirements"], lines["Requirements"]
        tline, rows = find_table(blocks, ["ID", "Requirement"])
        if tline is None:
            rep.add(sline, "E", "S3", "missing table: ID | Requirement")
        for rline, cells in rows:
            if len(cells) != 2:
                rep.add(rline, "E", "S3", "a requirement row has 2 cells")
                continue
            rid, text = cells
            if not re.fullmatch(r"R\d+", rid) or rid in ids:
                rep.add(rline, "E", "S3", f"ID \"{rid}\" must be R<number> and unique")
            ids.append(rid)
            plain = clean(text)
            if len(sentences(text)) != 1 or not any(p.match(plain) for p in EARS):
                rep.add(rline, "E", "S3", f"{rid} must be one sentence in an EARS pattern (see references/rules.md)")
            if len(re.findall(MODAL, plain)) != 1:
                rep.add(rline, "E", "S3", f"{rid} must have exactly one of MUST, SHOULD, MAY")
        if len(rows) > REQ_ROWS_MAX:
            rep.add(tline, "E", "L5", f"{len(rows)} requirements, maximum is {REQ_ROWS_MAX}; split the spec")
        elif len(rows) > REQ_ROWS_WARN:
            rep.add(tline, "W", "L5", f"{len(rows)} requirements; consider a split above {REQ_ROWS_WARN}")

    # S4 Example
    if "Example" in sections and not any(k == "code" for k, _, _ in sections["Example"]):
        rep.add(lines["Example"], "E", "S4", "Example needs one real input and output in a code block")

    # S5 Cases
    if "Cases" in sections:
        blocks, sline = sections["Cases"], lines["Cases"]
        cline, cases = find_table(blocks, ["Given", "When", "Then", "Covers"])
        if cline is None:
            rep.add(sline, "E", "S5", "missing table: Given | When | Then | Covers")
        covered = set()
        for rline, cells in cases:
            refs = [r.strip() for r in cells[-1].split(",")]
            for ref in refs:
                if ref != UNCHANGED and ref not in ids:
                    rep.add(rline, "E", "S5", f"Covers names \"{ref}\"; use a requirement ID or \"{UNCHANGED}\"")
            covered.update(refs)
        for rid in ids:
            if cline is not None and rid not in covered:
                rep.add(cline, "E", "S5", f"{rid} has no row in the cases table")
        if cline is not None and UNCHANGED not in covered:
            rep.add(cline, "W", "S5", f"no case protects existing behaviour; add a row that covers \"{UNCHANGED}\"")

    # S6 Check
    if "Check" in sections and not any(k in ("para", "bullet", "code") for k, _, _ in sections["Check"]):
        rep.add(lines["Check"], "E", "S6", "Check is empty; give the steps and the result that proves the change")

    # S8 paths
    if repo:
        for number, line in enumerate(raw.split("\n"), 1):
            for m in PATH.finditer(line):
                if not (Path(repo) / m.group(1)).exists():
                    rep.add(number, "E", "S8", f"path does not exist: {m.group(1)}")
    return rep


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("spec")
    ap.add_argument("--glossary", help="default: glossary.md next to the spec")
    ap.add_argument("--repo", help="check that each file path in the spec exists here")
    ap.add_argument("--strict", action="store_true", help="warnings also fail")
    args = ap.parse_args()
    glossary = args.glossary or str(Path(args.spec).parent / "glossary.md")
    rep = lint(args.spec, glossary, args.repo)
    print(f"{rep.errors} errors, {rep.warnings} warnings")
    sys.exit(1 if rep.errors or (args.strict and rep.warnings) else 0)


if __name__ == "__main__":
    main()
