#!/usr/bin/env python3
"""Render a spec as one self-contained HTML page. Standard library only.

Usage: view.py SPEC.md [--glossary glossary.md] [-o OUT.html] [--open]

The page shows the skim layer open and the build layer collapsed, links each
case to the requirements that it covers, and explains glossary terms on hover.
"""
import argparse
import contextlib
import html
import io
import re
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import spec_lint  # noqa: E402

SKIM = ["Why", "Example", "Check"]
esc = html.escape


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def parse(text):
    """Return (title, meta, sections). A section is {name, summary, blocks}."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    title, meta, sections, cur = "", {}, [], None
    lines, i = text.split("\n"), 0

    def add(block):
        if cur is not None:
            cur["blocks"].append(block)

    while i < len(lines):
        line = lines[i].rstrip()
        s = line.strip()
        if s.startswith("```"):
            lang, body = s[3:].strip(), []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            add(("code", lang, "\n".join(body)))
        elif s.startswith("# "):
            title = re.sub(r"^Spec:\s*", "", s[2:].strip())
        elif s.startswith("## "):
            cur = {"name": s[3:].strip(), "summary": None, "blocks": []}
            sections.append(cur)
        elif s.startswith("### "):
            add(("h3", s[4:].strip()))
        elif s in ("<details>", "</details>") or not s:
            pass
        elif re.fullmatch(r"<summary>.*</summary>", s):
            if cur is not None:
                cur["summary"] = s[9:-10].strip()
        elif s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = spec_lint.split_row(lines[i])
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            add(("table", rows[0], rows[1:]))
            continue
        elif re.match(r"(-|\d+\.)\s+", s):
            kind = "ol" if s[0].isdigit() else "ul"
            items = []
            while i < len(lines) and re.match(r"(-|\d+\.)\s+", lines[i].strip()):
                items.append(re.sub(r"^(-|\d+\.)\s+", "", lines[i].strip()))
                i += 1
            add((kind, items))
            continue
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not re.match(r"(#|\||```|<|-\s|\d+\.\s)", lines[i].strip()):
                para.append(lines[i].strip())
                i += 1
            joined = " ".join(para)
            if cur is None and "**Status:**" in joined:
                for part in joined.split("·"):
                    m = re.match(r"\s*\*\*(.+?):\*\*\s*(.*)", part)
                    if m:
                        meta[m.group(1)] = m.group(2).strip()
            else:
                add(("p", joined))
            continue
        i += 1
    return title, meta, sections


def load_glossary(path):
    terms = {}
    if path and Path(path).exists():
        _, _, sections = parse("## g\n" + Path(path).read_text())
        for sec in sections:
            for block in sec["blocks"]:
                if block[0] == "table" and [c.lower() for c in block[1]][:2] == ["term", "meaning"]:
                    for row in block[2]:
                        terms[row[0]] = row[1]
    return terms


class Renderer:
    def __init__(self, terms, req_ids):
        self.terms, self.req_ids = terms, req_ids
        names = sorted(terms, key=len, reverse=True)
        self.term_re = re.compile(r"\b(" + "|".join(re.escape(n) for n in names) + r")(s?)\b", re.I) if names else None
        self.lookup = {n.lower(): n for n in names}

    def plain(self, text):
        return re.sub(r"[`*]", "", text)

    def _text(self, chunk):
        out = esc(chunk)
        out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
        out = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', out)
        pieces = re.split(r"(<[^>]+>)", out)
        for n, piece in enumerate(pieces):
            if piece.startswith("<"):
                continue
            piece = re.sub(r"\b(MUST NOT|SHOULD NOT|MUST|SHOULD|MAY)\b",
                           lambda m: f'<b class="modal {m.group(1).split()[0].lower()}">{m.group(1)}</b>', piece)
            piece = re.sub(r"\bR\d+\b", lambda m: self.req(m.group(0)) if m.group(0) in self.req_ids else m.group(0), piece)
            if self.term_re:
                piece = "".join(self._terms(p) if not p.startswith("<") else p for p in re.split(r"(<[^>]+>[^<]*</[^>]+>)", piece))
            pieces[n] = piece
        return "".join(pieces)

    def _terms(self, piece):
        def wrap(m):
            name = self.lookup[m.group(1).lower()]
            return (f'<span class="term" tabindex="0" data-def="{esc(self.plain(self.terms[name]), quote=True)}">'
                    f'{m.group(1)}{m.group(2)}</span>')
        return self.term_re.sub(wrap, piece)

    def inline(self, text):
        parts = re.split(r"(`[^`]*`)", text)
        return "".join(f"<code>{esc(p[1:-1])}</code>" if len(p) > 1 and p[0] == "`" and p[-1] == "`" else self._text(p)
                       for p in parts)

    def req(self, rid):
        return f'<a class="rid" href="#{rid}" data-req="{rid}">{rid}</a>'


def render(title, meta, sections, terms, source, lint):
    reqs, cases = {}, {}
    for sec in sections:
        for block in sec["blocks"]:
            if block[0] != "table":
                continue
            head = [c.lower() for c in block[1]]
            if head == ["id", "requirement"]:
                for row in block[2]:
                    reqs[row[0]] = row[1]
            elif head and head[-1] == "covers":
                for row in block[2]:
                    for ref in (r.strip() for r in row[-1].split(",")):
                        cases[ref] = cases.get(ref, 0) + 1
    r = Renderer(terms, set(reqs))
    case_no = 0

    def block_html(block, sec):
        nonlocal case_no
        kind = block[0]
        if kind == "p":
            return f"<p>{r.inline(block[1])}</p>"
        if kind == "h3":
            return f'<h3 id="{slug(sec["name"])}-{slug(block[1])}">{esc(block[1])}</h3>'
        if kind == "code":
            first = block[2].strip().split("\n")[0] if block[2].strip() else ""
            label = "Response" if first.startswith("HTTP/") else ("Request" if block[1] == "http" else (block[1] or "Code"))
            return (f'<figure class="code"><figcaption><span>{esc(label)}</span>'
                    f'<button type="button" class="copy">Copy</button></figcaption>'
                    f"<pre><code>{esc(block[2])}</code></pre></figure>")
        if kind == "ol":
            return '<ol class="steps">' + "".join(f"<li><div>{r.inline(i)}</div></li>" for i in block[1]) + "</ol>"
        if kind == "ul":
            rows = []
            for item in block[1]:
                m = re.match(r"\*\*(.+?)\*\*\s*(.*)", item)
                if m:
                    rows.append(f'<div class="fact"><dt>{esc(m.group(1).rstrip("."))}</dt><dd>{r.inline(m.group(2))}</dd></div>')
                else:
                    rows.append(f'<div class="fact plain"><dd>{r.inline(item)}</dd></div>')
            return f'<dl class="facts">{"".join(rows)}</dl>'
        head = [c.lower() for c in block[1]]
        if head == ["id", "requirement"]:
            out = []
            for rid, text in block[2]:
                n = cases.get(rid, 0)
                note = f'{n} case{"" if n == 1 else "s"}' if n else "no case"
                out.append(f'<li id="{rid}" class="req" data-covers="{rid}"><span class="rid" data-req="{rid}">{rid}</span>'
                           f'<div><p>{r.inline(text)}</p><a class="cases-link" href="#cases" data-req="{rid}">{note}</a></div></li>')
            return f'<ul class="reqs">{"".join(out)}</ul>'
        if head and head[-1] == "covers":
            rows = []
            for row in block[2]:
                case_no += 1
                refs = [x.strip() for x in row[-1].split(",")]
                chips = "".join(r.req(x) if x in reqs else f'<span class="unchanged">{esc(x)}</span>' for x in refs)
                cells = "".join(f'<td data-label="{esc(h)}">{r.inline(c)}</td>' for h, c in zip(block[1][:-1], row[:-1]))
                rows.append(f'<tr id="case-{case_no}" data-covers="{" ".join(refs)}">{cells}<td data-label="Covers" class="covers">{chips}</td></tr>')
            ths = "".join(f"<th>{esc(h)}</th>" for h in block[1])
            return f'<div class="table-wrap"><table class="cases"><thead><tr>{ths}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
        ths = "".join(f"<th>{esc(h)}</th>" for h in block[1])
        trs = "".join("<tr>" + "".join(f"<td>{r.inline(c)}</td>" for c in row) + "</tr>" for row in block[2])
        return f'<div class="table-wrap"><table><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table></div>'

    nav, body = {"Skim": [], "Build": []}, []
    for sec in sections:
        sid = slug(sec["name"])
        layer = "Skim" if sec["name"] in SKIM else "Build"
        groups = [b[1] for b in sec["blocks"] if b[0] == "h3"]
        sub = "".join(f'<li><a href="#{sid}-{slug(g)}">{esc(g)}</a></li>' for g in groups)
        nav[layer].append(f'<li><a href="#{sid}">{esc(sec["name"])}</a>{f"<ul>{sub}</ul>" if sub else ""}</li>')
        inner = "".join(block_html(b, sec) for b in sec["blocks"])
        if sec["summary"]:
            inner = f'<details class="more"><summary><span>{esc(sec["summary"])}</span></summary><div class="more-body">{inner}</div></details>'
        body.append(f'<section id="{sid}" class="{layer.lower()}"><h2>{esc(sec["name"])}</h2>{inner}</section>')
    if terms:
        rows = "".join(f'<div class="fact"><dt>{esc(t)}</dt><dd>{r.inline(m)}</dd></div>' for t, m in terms.items())
        nav["Build"].append('<li><a href="#glossary">Glossary</a></li>')
        body.append(f'<section id="glossary" class="build"><h2>Glossary</h2><details class="more"><summary><span>Show the {len(terms)} '
                    f'glossary terms</span></summary><div class="more-body"><dl class="facts">{rows}</dl></div></details></section>')

    status = meta.get("Status", "")
    errors, warnings, findings = lint
    lint_label = "Lint passes" if not errors and not warnings else f"{errors} lint error{'' if errors == 1 else 's'}, {warnings} warning{'' if warnings == 1 else 's'}"
    lint_panel = ""
    if findings:
        items = "".join(f"<li><code>{esc(f)}</code></li>" for f in findings)
        lint_panel = f'<details class="lint-panel"><summary><span>Show the {len(findings)} lint findings</span></summary><ul>{items}</ul></details>'
    facts = "".join(f"<div><dt>{esc(k)}</dt><dd>{r.inline(v)}</dd></div>" for k, v in meta.items() if k != "Status")
    navs = "".join(f'<div class="layer"><p>{name}</p><ul>{"".join(items)}</ul></div>' for name, items in nav.items() if items)
    return PAGE.format(title=esc(title), status=esc(status), status_class=slug(status), facts=facts, nav=navs,
                       body="".join(body), lint_label=esc(lint_label), lint_class="ok" if not errors else "bad",
                       lint_panel=lint_panel, source=esc(source), css=CSS, js=JS)


CSS = r"""
:root{--bg:#fff;--panel:#fafafa;--fg:#161616;--soft:#5f6368;--line:#e8e8e8;--accent:#1f5fd1;--accent-bg:#edf3fe;
--must:#161616;--should:#9a5b00;--ok:#0f7b46;--ok-bg:#e9f7ef;--bad:#b42318;--bad-bg:#fdecea;--lit:#fff7d6;--code:#f5f5f5;
--sans:"Inter","Geist",ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
--mono:"Geist Mono","JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
:root[data-theme="dark"]{--bg:#0b0c0e;--panel:#121417;--fg:#ededed;--soft:#9aa0a6;--line:#24272c;--accent:#8ab4ff;--accent-bg:#152238;
--must:#fff;--should:#f0b35a;--ok:#5fd39a;--ok-bg:#10281d;--bad:#ff8a80;--bad-bg:#3a1512;--lit:#3a3210;--code:#16181c}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0b0c0e;--panel:#121417;--fg:#ededed;--soft:#9aa0a6;--line:#24272c;
--accent:#8ab4ff;--accent-bg:#152238;--must:#fff;--should:#f0b35a;--ok:#5fd39a;--ok-bg:#10281d;--bad:#ff8a80;--bad-bg:#3a1512;--lit:#3a3210;--code:#16181c}}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:76px}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.65 var(--sans);-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:4px}
code{font:13px/1.5 var(--mono);background:var(--code);padding:.1em .35em;border-radius:5px}
header.bar{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:12px;height:56px;padding:0 20px;
background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.bar .name{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.bar .kind{color:var(--soft);font-weight:500}.bar .gap{flex:1}
.badge{font-size:12.5px;font-weight:550;padding:3px 10px;border-radius:999px;border:1px solid var(--line);white-space:nowrap}
.badge.approved,.badge.implemented,.badge.ok{color:var(--ok);background:var(--ok-bg);border-color:transparent}
.badge.bad{color:var(--bad);background:var(--bad-bg);border-color:transparent}
.bar button{font:inherit;font-size:13px;color:var(--fg);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:5px 11px;cursor:pointer}
.bar button:hover{background:var(--panel)}
.shell{display:grid;grid-template-columns:260px minmax(0,1fr);max-width:1180px;margin:0 auto}
nav.side{position:sticky;top:56px;align-self:start;padding:28px 20px 40px}
.shell{background:linear-gradient(var(--line),var(--line)) 260px 0/1px 100% no-repeat}
.layer+.layer{margin-top:26px}.layer>p{margin:0 0 6px 10px;font-size:12.5px;color:var(--soft);font-weight:550}
nav ul{list-style:none;margin:0;padding:0}nav li a{display:block;padding:5px 10px;border-radius:7px;color:var(--fg);font-size:14px}
nav li a:hover{background:var(--panel);text-decoration:none}nav li a.here{background:var(--accent-bg);color:var(--accent);font-weight:550}
nav ul ul{margin:2px 0 6px 10px;border-left:1px solid var(--line)}nav ul ul a{color:var(--soft);font-size:13.5px;padding:3px 12px}
main{padding:44px 56px 120px;max-width:820px;min-width:0}
h1{font-size:34px;line-height:1.12;letter-spacing:-.025em;font-weight:680;margin:0 0 18px;text-wrap:balance}
dl.meta{display:flex;flex-wrap:wrap;gap:8px 28px;margin:0 0 8px;font-size:14px}dl.meta div{display:flex;gap:8px}
dl.meta dt{color:var(--soft)}dl.meta dd{margin:0}
section{padding-top:38px}h2{font-size:21px;letter-spacing:-.012em;font-weight:650;margin:0 0 12px}
section.build h2{display:flex;align-items:baseline;gap:10px}
h3{font-size:14px;font-weight:620;margin:26px 0 10px;color:var(--fg)}
p{margin:0 0 12px;max-width:68ch}
.divide{margin:52px 0 0;padding-top:18px;border-top:1px solid var(--line);color:var(--soft);font-size:13.5px}
figure.code{margin:14px 0;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--panel)}
figure.code figcaption{display:flex;justify-content:space-between;align-items:center;padding:7px 12px;border-bottom:1px solid var(--line);font-size:12.5px;color:var(--soft)}
figure.code pre{margin:0;padding:14px 16px;overflow:auto}figure.code code{background:none;padding:0;font-size:13px}
.copy{font:inherit;font-size:12px;color:var(--soft);background:none;border:1px solid var(--line);border-radius:6px;padding:2px 8px;cursor:pointer}
ol.steps{list-style:none;counter-reset:s;margin:6px 0 0;padding:0}
ol.steps li{counter-increment:s;display:grid;grid-template-columns:28px 1fr;gap:12px;padding:0 0 16px;position:relative}
ol.steps li::before{content:counter(s);width:26px;height:26px;border-radius:50%;border:1px solid var(--line);background:var(--bg);
display:grid;place-items:center;font-size:12.5px;font-weight:600;z-index:1}
ol.steps li:not(:last-child)::after{content:"";position:absolute;left:13px;top:26px;bottom:0;width:1px;background:var(--line)}
details.more{border:1px solid var(--line);border-radius:12px;background:var(--bg)}
details.more>summary{list-style:none;cursor:pointer;padding:12px 16px;display:flex;align-items:center;gap:10px;font-weight:560;font-size:14.5px;border-radius:12px}
details.more>summary::-webkit-details-marker{display:none}
details.more>summary::before{content:"";width:7px;height:7px;border-right:1.6px solid var(--soft);border-bottom:1.6px solid var(--soft);
transform:rotate(-45deg);transition:transform .15s}
details.more[open]>summary::before{transform:rotate(45deg)}details.more>summary:hover{background:var(--panel)}
details.more[open]>summary{border-bottom:1px solid var(--line);border-radius:12px 12px 0 0}
.more-body{padding:4px 18px 18px}.more-body>h3:first-child{margin-top:18px}
ul.reqs{list-style:none;margin:0;padding:0;border:1px solid var(--line);border-radius:10px;overflow:hidden}
li.req{display:grid;grid-template-columns:44px 1fr;gap:12px;padding:13px 14px;transition:background .15s}li.req+li.req{border-top:1px solid var(--line)}
li.req p{margin:0 0 4px;max-width:none}.cases-link{font-size:12.5px;color:var(--soft)}
.rid{display:inline-grid;place-items:center;min-width:34px;height:22px;padding:0 7px;border-radius:6px;background:var(--accent-bg);
color:var(--accent);font:600 12px/1 var(--mono);text-decoration:none!important}
b.modal{font-weight:700;color:var(--must);letter-spacing:.01em}b.modal.should{color:var(--should)}b.modal.may{color:var(--soft)}
dl.facts{margin:0;border:1px solid var(--line);border-radius:10px;overflow:hidden}
.fact{display:grid;grid-template-columns:190px 1fr;gap:16px;padding:12px 14px}.fact+.fact{border-top:1px solid var(--line)}
.fact.plain{grid-template-columns:1fr}.fact dt{font-weight:600;font-size:14px}.fact dd{margin:0}
.table-wrap{border:1px solid var(--line);border-radius:10px;overflow:auto}
table{border-collapse:collapse;width:100%;font-size:14px}th{text-align:left;font-weight:600;font-size:12.5px;color:var(--soft);background:var(--panel)}
th,td{padding:10px 12px;vertical-align:top;border-bottom:1px solid var(--line)}tbody tr:last-child td{border-bottom:0}
tbody tr{transition:background .15s}td.covers{white-space:nowrap}td.covers .rid{margin-right:4px}
.unchanged{font-size:12px;color:var(--soft);border:1px dashed var(--line);border-radius:6px;padding:2px 7px}
.lit{background:var(--lit)!important}
.term{border-bottom:1px dotted var(--soft);cursor:help;position:relative}
.term:hover::after,.term:focus::after{content:attr(data-def);position:absolute;left:0;top:calc(100% + 6px);z-index:9;width:max-content;max-width:320px;
padding:8px 10px;border-radius:8px;background:var(--fg);color:var(--bg);font:13px/1.45 var(--sans);white-space:normal;box-shadow:0 6px 24px rgba(0,0,0,.18)}
.lint-panel{margin:14px 0 0;font-size:13.5px}.lint-panel summary{cursor:pointer;color:var(--bad)}.lint-panel ul{padding-left:18px}
footer{margin-top:64px;color:var(--soft);font-size:13px}
@media (max-width:860px){.shell{grid-template-columns:1fr}nav.side{position:static;border-bottom:1px solid var(--line);padding:12px 16px}.shell{background:none}
.layer{display:inline-block;vertical-align:top;margin:0 18px 0 0!important}nav ul ul{display:none}main{padding:28px 18px 80px}h1{font-size:27px}
.fact{grid-template-columns:1fr;gap:2px}.bar .kind,.bar .lint{display:none}
table.cases thead{display:none}table.cases tr{display:block;border-bottom:1px solid var(--line)}table.cases td{display:grid;grid-template-columns:70px 1fr;gap:10px;border:0;padding:6px 12px}
table.cases td::before{content:attr(data-label);color:var(--soft);font-size:12.5px}}
@media print{header.bar,nav.side,.copy{display:none}.shell{display:block}main{padding:0;max-width:none}}
"""

JS = r"""
const root=document.documentElement,key='agent-spec-theme';
try{const t=localStorage.getItem(key);if(t)root.dataset.theme=t}catch(e){}
const dark=()=>root.dataset.theme?root.dataset.theme==='dark':matchMedia('(prefers-color-scheme:dark)').matches;
const themeBtn=document.getElementById('theme');
const paint=()=>themeBtn.textContent=dark()?'Light theme':'Dark theme';paint();
themeBtn.onclick=()=>{root.dataset.theme=dark()?'light':'dark';try{localStorage.setItem(key,root.dataset.theme)}catch(e){}paint()};
const all=[...document.querySelectorAll('details.more')];
const label=d=>{const s=d.querySelector('summary span');s.textContent=s.textContent.replace(/^(Show|Hide)\b/,d.open?'Hide':'Show')};
all.forEach(d=>d.addEventListener('toggle',()=>{label(d);sync()}));
const allBtn=document.getElementById('all');
const sync=()=>allBtn.textContent=all.every(d=>d.open)?'Collapse the detail':'Expand the detail';
allBtn.onclick=()=>{const open=!all.every(d=>d.open);all.forEach(d=>d.open=open)};sync();
const reveal=id=>{const el=document.getElementById(id);if(!el)return;const d=el.closest('details')||el.querySelector('details');
if(d&&el.closest('details')&&!d.open)d.open=true;return el};
const go=()=>{const id=decodeURIComponent(location.hash.slice(1));if(id){const el=reveal(id);if(el)el.scrollIntoView()}};
addEventListener('hashchange',go);go();
document.querySelectorAll('nav a').forEach(a=>a.addEventListener('click',()=>reveal(a.getAttribute('href').slice(1))));
const mark=(id,on)=>document.querySelectorAll('[data-covers~="'+id+'"]').forEach(e=>e.classList.toggle('lit',on));
document.querySelectorAll('[data-req]').forEach(el=>{const id=el.dataset.req;
el.addEventListener('mouseenter',()=>mark(id,true));el.addEventListener('mouseleave',()=>mark(id,false));
el.addEventListener('focus',()=>mark(id,true));el.addEventListener('blur',()=>mark(id,false));
if(el.classList.contains('cases-link'))el.addEventListener('click',e=>{e.preventDefault();
const row=document.querySelector('tr[data-covers~="'+id+'"]');if(row){row.closest('details').open=true;row.scrollIntoView({block:'center'});
mark(id,true);setTimeout(()=>mark(id,false),1800)}})});
document.querySelectorAll('.copy').forEach(b=>b.onclick=()=>navigator.clipboard.writeText(b.closest('figure').querySelector('code').textContent)
.then(()=>{b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1200)}));
const links=[...document.querySelectorAll('nav.side>.layer>ul>li>a')];
const seen=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)links.forEach(a=>a.classList.toggle('here',a.getAttribute('href')==='#'+e.target.id))}),
{rootMargin:'-20% 0px -70% 0px'});document.querySelectorAll('main section').forEach(s=>seen.observe(s));
addEventListener('beforeprint',()=>all.forEach(d=>d.open=true));
"""

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{css}</style></head><body>
<header class="bar"><span class="name"><span class="kind">Spec</span> &nbsp;{title}</span><span class="gap"></span>
<span class="badge lint {lint_class}">{lint_label}</span><span class="badge {status_class}">{status}</span>
<button type="button" id="all">Expand the detail</button><button type="button" id="theme">Dark theme</button></header>
<div class="shell"><nav class="side" aria-label="Sections">{nav}</nav>
<main><h1>{title}</h1><dl class="meta">{facts}</dl>{lint_panel}{body}
<footer>Rendered from {source}. Hover a requirement to light the cases that cover it.</footer></main></div>
<script>{js}</script></body></html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("spec")
    ap.add_argument("--glossary", help="default: glossary.md next to the spec")
    ap.add_argument("-o", "--out", help="default: the spec path with .html")
    ap.add_argument("--open", action="store_true", help="open the page in a browser")
    args = ap.parse_args()
    spec = Path(args.spec)
    glossary = args.glossary or str(spec.parent / "glossary.md")
    title, meta, sections = parse(spec.read_text())
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rep = spec_lint.lint(str(spec), glossary, None)
    findings = [re.sub(r"^.*?:(\d+): ", r"line \1: ", line) for line in buf.getvalue().splitlines()]
    page = render(title, meta, sections, load_glossary(glossary), spec.name, (rep.errors, rep.warnings, findings))
    out = Path(args.out) if args.out else spec.with_suffix(".html")
    out.write_text(page)
    print(out)
    if args.open:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
