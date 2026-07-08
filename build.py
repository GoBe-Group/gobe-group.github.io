#!/usr/bin/env python3
"""Build GoBe's public legal/support site from the source markdown.

Run:  python3 build.py
Outputs: index.html, privacy.html, terms.html, support.html

The privacy/terms pages are generated from the same markdown files that are kept
word-for-word in sync with the in-app Swift docs. Internal editor notes (lines
starting with '>') are stripped from the public pages. Re-run after editing the
.md files.
"""
import html
import re
from pathlib import Path

HERE = Path(__file__).parent
CONTACT = "hamedbakayoko048@gmail.com"

CSS = """
:root{
  /* Exact GoBe design-system values (GoBeColors.swift) */
  --paper:#E8DCC4; --paper-light:#F5EBD3; --paper-aged:#D6C49F;
  --cardboard:#B88C58; --cardboard-dark:#7E5A32;
  --ink:#2B241D; --ink-muted:#6F675A;
  --go:#5E8205; --go-bright:#90C808; --be:#2F7BFF; --be-dark:#154AA8;
  --stamp:#E89135; --red:#E84C3D;
  --border:rgba(126,90,50,.35); --border-soft:rgba(126,90,50,.25);
  --shadow:rgba(43,36,29,.16);
  --serif:'Cormorant Garamond',Georgia,'Times New Roman',serif;
  --sans:'Avenir Next','Avenir','Mulish','Segoe UI',system-ui,-apple-system,sans-serif;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:var(--sans); font-size:17px; line-height:1.62;
  -webkit-font-smoothing:antialiased;
}
/* barely-there paper fibre grain, matching the app's paperGrain() pass */
body::before{
  content:""; position:fixed; inset:0; pointer-events:none; z-index:9999;
  opacity:.035; mix-blend-mode:multiply;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
.wrap{max-width:700px; margin:0 auto; padding:38px 22px 80px}

header.site{position:relative; border-bottom:1px solid var(--border); padding-bottom:18px; margin-bottom:34px}
/* washi-tape strip taped over the header, like the app's card headers */
header.site::before{
  content:""; position:absolute; top:-14px; right:26px; width:76px; height:17px;
  background:var(--go-bright); opacity:.72; transform:rotate(-2.5deg);
  box-shadow:inset 0 0 0 .5px rgba(126,90,50,.4);
  background-image:repeating-linear-gradient(90deg,rgba(255,255,255,.16) 0 1px,transparent 1px 8px);
}
.brand{display:inline-flex; align-items:center; text-decoration:none}
.brand img{height:56px; width:auto; display:block}
nav.top{margin-top:13px; font-size:12px; text-transform:uppercase; letter-spacing:1.2px; font-weight:600}
nav.top a{color:var(--ink-muted); text-decoration:none; margin-right:20px; padding-bottom:3px; border-bottom:2px solid transparent}
nav.top a:hover{color:var(--ink)}

h1{font-family:var(--serif); font-weight:700; font-size:44px; line-height:1.08; letter-spacing:.2px; margin:0 0 10px}
h2{font-family:var(--serif); font-weight:700; font-size:27px; line-height:1.15; margin:40px 0 12px; color:var(--ink)}
p{margin:0 0 16px}
ul{margin:0 0 16px; padding-left:22px}
li{margin:0 0 9px}
a{color:var(--be)}
strong{font-weight:700}

/* Passport-style stamp, used for the "Last updated" line */
.stamp{display:inline-block; font-size:12px; font-weight:700; letter-spacing:1.4px;
  text-transform:uppercase; color:var(--stamp); border:1.5px solid rgba(232,145,53,.55);
  border-radius:4px; padding:5px 10px; transform:rotate(-1.5deg); margin:0 0 26px}

/* paperLight card with warm printed edge + soft ink shadow */
.card{background:var(--paper-light); border:1px solid var(--border-soft);
  border-radius:26px; padding:26px 28px; margin:0 0 24px;
  box-shadow:0 16px 34px rgba(43,36,29,.14), 0 2px 0 rgba(255,255,255,.55) inset}
.card h2{margin-top:0}
.lede{font-size:20px; color:var(--ink-muted); margin:0 0 26px; line-height:1.45}

footer.site{border-top:1px solid var(--border); margin-top:56px; padding-top:20px; color:var(--ink-muted); font-size:13.5px; line-height:1.55}
footer.site a{color:var(--ink-muted)}

/* Chunky sticker CTA — white die-cut face, coloured under-edge, uppercase ink label */
.btn{display:inline-block; background:#fff; color:var(--ink)!important; text-decoration:none;
  text-transform:uppercase; letter-spacing:.09em; font-weight:700; font-size:13px;
  padding:14px 24px; border-radius:14px; border:1px solid var(--border-soft);
  box-shadow:0 4px 0 rgba(47,123,255,.38), 0 8px 14px var(--shadow); margin:8px 0 6px;
  transition:transform .08s ease, box-shadow .08s ease}
.btn:active{transform:translateY(3px); box-shadow:0 1px 0 rgba(47,123,255,.38), 0 3px 6px var(--shadow)}
.mono{font-family:'Avenir Next','Avenir',var(--sans); font-size:15px; color:var(--ink-muted); letter-spacing:.3px}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Mulish:wght@400;600;700;800&display=swap" rel="stylesheet">')


def page(title, body, active=""):
    def nav(href, label):
        cls = ' style="color:var(--accent);border-bottom-color:var(--accent)"' if active == href else ""
        return f'<a href="{href}"{cls}>{label}</a>'
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · GoBe</title>
<meta name="description" content="GoBe — leave and find traces of daily moments. {html.escape(title)}.">
<link rel="icon" type="image/png" href="assets/icon.png">
<link rel="apple-touch-icon" href="assets/icon.png">
{FONTS}
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="site">
<a class="brand" href="index.html"><img src="assets/gobe-logo.png" alt="GoBe" width="84" height="56"></a>
<nav class="top">{nav('index.html','Home')}{nav('privacy.html','Privacy')}{nav('terms.html','Terms')}{nav('support.html','Support')}</nav>
</header>
{body}
<footer class="site">
<p>GoBe is operated by Hamed Bakayoko, sole trader trading as GoBe, 35 Cheshire Close, CR4 1XF, United Kingdom.<br>
Contact: <a href="mailto:{CONTACT}">{CONTACT}</a> · Governing law: England &amp; Wales.</p>
</footer>
</div>
</body>
</html>
"""


def inline(text):
    text = html.escape(text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    return text


def md_to_html(md):
    """Minimal converter: ## headings, - lists, **bold**, [links], paragraphs.
    Skips the H1 and any blockquote (>) internal editor notes."""
    lines = md.splitlines()
    out, para, in_list = [], [], False

    def flush_para():
        nonlocal para
        if para:
            joined = ' '.join(para).strip()
            # Render the "Last updated" line as a passport-style stamp
            m = re.match(r'\*\*Last updated:\*\*\s*(.+)', joined)
            if m:
                out.append(f'<div class="stamp">Last updated · {html.escape(m.group(1))}</div>')
            else:
                out.append(f"<p>{inline(joined)}</p>")
            para = []

    def flush_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith('# '):            # H1 — supplied by template
            continue
        if stripped.startswith('>'):             # internal note — drop
            continue
        if not stripped:
            flush_para(); flush_list(); continue
        if stripped.startswith('## '):
            flush_para(); flush_list()
            out.append(f"<h2>{inline(stripped[3:])}</h2>")
            continue
        if stripped.startswith('- '):
            flush_para()
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{inline(stripped[2:])}</li>")
            continue
        flush_list()
        para.append(stripped)
    flush_para(); flush_list()
    return "\n".join(out)


def build_legal(src, title, slug, active):
    md = (HERE / src).read_text(encoding="utf-8")
    body = f'<h1>{title}</h1>\n{md_to_html(md)}'
    (HERE / slug).write_text(page(title, body, active), encoding="utf-8")
    print("wrote", slug)


# --- Privacy & Terms (generated from markdown) ---
build_legal("gobe-privacy-policy.md", "Privacy Policy", "privacy.html", "privacy.html")
build_legal("gobe-terms-of-service.md", "Terms of Service", "terms.html", "terms.html")

# --- Support page ---
support = f"""<h1>Support</h1>
<p class="lede">Help with GoBe, and how to reach a real person.</p>
<div class="card">
<h2 style="margin-top:0">Contact</h2>
<p>GoBe is run by one person. The fastest way to get help, report a problem, or
ask a question is by email:</p>
<p><a class="btn" href="mailto:{CONTACT}?subject=GoBe%20support">Email support</a></p>
<p class="mono">{CONTACT}</p>
<p>We aim to reply within a few days.</p>
</div>
<h2>Common questions</h2>
<ul>
<li><strong>How do I delete my account?</strong> Open the app, go to your profile, then
Account, and choose <strong>Delete Account</strong>. This permanently removes your account,
trails, and traces.</li>
<li><strong>How do I control location?</strong> GoBe only records your route while you are
actively recording a trail. You can stop a recording, or change location permission any time
in iOS Settings &rsaquo; GoBe.</li>
<li><strong>What are protected areas?</strong> Places you mark (home, work, the gym) that stay
on your device only. GoBe warns you before you post a trace inside one.</li>
<li><strong>How do I report content or a user?</strong> Use the in-app report tools, or email
us at {CONTACT} with what the content is, where you found it, and why.</li>
</ul>
<h2>Legal</h2>
<p>See our <a href="privacy.html">Privacy Policy</a> and <a href="terms.html">Terms of Service</a>.</p>
"""
(HERE / "support.html").write_text(page("Support", support, "support.html"), encoding="utf-8")
print("wrote support.html")

# --- Home / landing ---
home = f"""<h1>Traces of your day, left where they happened.</h1>
<p class="lede">GoBe lets you record the paths you walk and drop short notes, photos,
and places along the way, then find the traces other people have left near you.</p>
<div class="card">
<p style="margin:0">GoBe is a small, independent app made in the UK. There are no ads and we
do not sell your data.</p>
</div>
<h2>Links</h2>
<ul>
<li><a href="privacy.html">Privacy Policy</a></li>
<li><a href="terms.html">Terms of Service</a></li>
<li><a href="support.html">Support &amp; contact</a></li>
</ul>
"""
(HERE / "index.html").write_text(page("Home", home, "index.html"), encoding="utf-8")
print("wrote index.html")
