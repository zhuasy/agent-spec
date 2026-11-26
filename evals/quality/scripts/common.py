"""Shared helpers for the spec-quality eval. Python standard library only.

Nothing in these scripts calls a model. Roles (spec-writer, implementer,
reader, judge) are run by the operator; the scripts only prepare folders and
score what the roles leave behind.
"""
import ast
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBLEMS = os.path.join(ROOT, "problems")
PROMPTS = os.path.join(ROOT, "prompts")
CANARY = "EVAL-CANARY-7f3a9c1e-quality"

SKIM_WORDS = 150          # the skim reader sees only this many words
READING_WPM = 200         # words per minute assumed for technical reading
TEST_TIMEOUT = 30         # seconds per single test
TEXT_EXT = {"", ".md", ".markdown", ".txt", ".rst", ".adoc", ".text", ".yaml", ".yml", ".json"}
ENTRY_FIRST = ("readme", "index", "spec", "prd", "overview", "summary")


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump_json(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=False)
        f.write("\n")


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def write_text(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def list_problems():
    return sorted(d for d in os.listdir(PROBLEMS)
                  if os.path.isfile(os.path.join(PROBLEMS, d, "problem.json")))


def problem_dir(name):
    """Accepts a full name or a unique prefix such as 'p3'."""
    matches = [p for p in list_problems() if p == name or p.startswith(name)]
    if len(matches) != 1:
        sys.exit("problem %r: expected one match, got %s (have: %s)"
                 % (name, matches, ", ".join(list_problems())))
    return os.path.join(PROBLEMS, matches[0])


def copy_tree(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"),
                    dirs_exist_ok=True)


def fill(template_name, **values):
    """Fill {{NAME}} placeholders in a prompt file."""
    text = read_text(os.path.join(PROMPTS, template_name))
    for key, value in values.items():
        text = text.replace("{{%s}}" % key, str(value))
    left = re.findall(r"\{\{[A-Z_]+\}\}", text)
    if left:
        sys.exit("prompt %s: unfilled placeholders %s" % (template_name, sorted(set(left))))
    return text


# ---------------------------------------------------------------- spec folder

def spec_files(spec_dir):
    """Text files of a spec folder in reading order.

    No file names or formats are assumed. Order: the file named in an optional
    one-line ENTRY file first; otherwise names starting with readme/index/
    spec/prd/overview/summary first; then alphabetical by relative path.
    """
    found = []
    for base, dirs, files in os.walk(spec_dir):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d != "__pycache__")
        for name in sorted(files):
            if name == "ENTRY" or name.startswith("."):
                continue
            path = os.path.join(base, name)
            if os.path.splitext(name)[1].lower() not in TEXT_EXT:
                continue
            if os.path.getsize(path) > 2_000_000:
                continue
            found.append(os.path.relpath(path, spec_dir))
    entry_path = os.path.join(spec_dir, "ENTRY")
    entry = read_text(entry_path).strip() if os.path.exists(entry_path) else None

    def rank(rel):
        if entry and os.path.normpath(rel) == os.path.normpath(entry):
            return (0, rel)
        stem = os.path.basename(rel).lower()
        top = os.sep not in rel
        if top and stem.startswith(ENTRY_FIRST):
            return (1, rel)
        return (2, rel)

    return sorted(found, key=rank)


def spec_text(spec_dir):
    return "\n\n".join(read_text(os.path.join(spec_dir, rel)) for rel in spec_files(spec_dir))


def first_words(text, n):
    """The text up to and including its n-th whitespace-separated word."""
    count = 0
    for match in re.finditer(r"\S+", text):
        count += 1
        if count == n:
            return text[:match.end()]
    return text


def tree_hash(folder):
    digest = hashlib.sha256()
    for base, dirs, files in os.walk(folder):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(base, name)
            digest.update(os.path.relpath(path, folder).encode())
            with open(path, "rb") as f:
                digest.update(f.read())
    return digest.hexdigest()[:16]


def has_canary(folder):
    """Relative paths of files under folder that contain the canary string."""
    hits = []
    needle = CANARY.encode()
    for base, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            path = os.path.join(base, name)
            try:
                with open(path, "rb") as f:
                    if needle in f.read():
                        hits.append(os.path.relpath(path, folder))
            except OSError:
                pass
    return hits


# ------------------------------------------------------------- quote checking

def normalise(text):
    """Lower-case, drop markdown decoration, collapse whitespace."""
    text = text.lower()
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"[*_`#>|]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def quote_found(quote, haystack_normalised):
    """True when quote (at least 8 characters after cleaning) occurs verbatim."""
    if not isinstance(quote, str):
        return False
    q = normalise(quote).strip(" .\"'")
    return len(q) >= 8 and q in haystack_normalised


# ------------------------------------------------------------------ run tests

def test_ids(test_file):
    """[(Class, method)] for every test method in a unittest file, via the AST
    (the file is not imported, so a broken implementation cannot hide tests)."""
    tree = ast.parse(read_text(test_file))
    ids = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef) and sub.name.startswith("test"):
                    ids.append((node.name, sub.name))
    return ids


def category_of(class_name):
    for prefix in ("Core", "Edge", "Keep"):
        if class_name.startswith(prefix):
            return prefix.lower()
    return "other"


def _run_one(workdir, dotted):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONSTARTUP")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        p = subprocess.run([sys.executable, "-m", "unittest", dotted], cwd=workdir, env=env,
                           capture_output=True, text=True, timeout=TEST_TIMEOUT)
    except subprocess.TimeoutExpired:
        return "timeout", "timed out after %ds" % TEST_TIMEOUT
    tail = p.stderr.strip().splitlines()[-1:] or [""]
    if p.returncode == 0 and tail[0].startswith("OK") and "skipped" not in tail[0]:
        return "pass", ""
    return "fail", p.stderr[-1500:]


def run_test_modules(repo_dir, modules):
    """Run unittest files against a copy of repo_dir, one process per test.

    modules: list of (source_file, path_inside_repo_copy). Returns a list of
    {"id", "class", "category", "status", "detail"}.
    """
    with tempfile.TemporaryDirectory(prefix="spec-eval-") as tmp:
        work = os.path.join(tmp, "repo")
        copy_tree(repo_dir, work)
        jobs = []
        for source, rel in modules:
            target = os.path.join(work, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(source, target)
            module = rel[:-3].replace(os.sep, ".")
            for cls, method in test_ids(source):
                jobs.append((cls, "%s.%s.%s" % (module, cls, method), "%s.%s" % (cls, method)))
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            outcomes = list(pool.map(lambda job: _run_one(work, job[1]), jobs))
    return [{"id": short, "class": cls, "category": category_of(cls),
             "status": status, "detail": detail}
            for (cls, _, short), (status, detail) in zip(jobs, outcomes)]


def hidden_modules(pdir):
    hidden = os.path.join(pdir, "hidden")
    return [(os.path.join(hidden, n), "_eval_hidden_" + n)
            for n in sorted(os.listdir(hidden)) if n.endswith(".py")]


def visible_modules(pdir):
    """The starter's own tests, taken from the pristine starter (an implementer
    may have edited or deleted its copy)."""
    tests = os.path.join(pdir, "starter", "tests")
    return [(os.path.join(tests, n), os.path.join("tests", n))
            for n in sorted(os.listdir(tests)) if n.startswith("test") and n.endswith(".py")]


def score_repo(pdir, repo_dir):
    """Hidden and visible test results for an implementation of problem pdir."""
    baseline = load_json(os.path.join(pdir, "baseline.json"), {}).get("kind", {})
    hidden = run_test_modules(repo_dir, hidden_modules(pdir))
    for t in hidden:
        t["kind"] = baseline.get(t["id"], "new")
    visible = run_test_modules(repo_dir, visible_modules(pdir))

    def rate(tests):
        return round(sum(t["status"] == "pass" for t in tests) / len(tests), 4) if tests else None

    new = [t for t in hidden if t["kind"] == "new"]
    kept = [t for t in hidden if t["kind"] == "regression"]
    summary = {
        "hidden_total": len(hidden),
        "hidden_passed": sum(t["status"] == "pass" for t in hidden),
        "hidden_pass_rate": rate(hidden),
        "new_behaviour_pass_rate": rate(new),
        "new_behaviour_tests": len(new),
        "regression_pass_rate": rate(kept),
        "regression_tests": len(kept),
        "visible_pass_rate": rate(visible),
        "visible_tests": len(visible),
        "all_green": all(t["status"] == "pass" for t in hidden + visible),
        "timeouts": sum(t["status"] == "timeout" for t in hidden + visible),
    }
    for cat in ("core", "edge", "keep"):
        summary["%s_pass_rate" % cat] = rate([t for t in hidden if t["category"] == cat])
    return {"summary": summary, "hidden": hidden, "visible": visible}


# ---------------------------------------------------------------- run folders

def run_meta(run_dir):
    meta = load_json(os.path.join(run_dir, "run.json"))
    if meta is None:
        sys.exit("%s is not a run folder (no run.json)" % run_dir)
    return meta


def frozen_spec(run_dir):
    path = os.path.join(run_dir, "spec_frozen")
    if not os.path.isdir(path):
        sys.exit("%s has no spec_frozen/ - run stage_run.py first" % run_dir)
    return path
