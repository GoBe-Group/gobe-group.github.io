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
  --paper:#f5efe2; --paper-2:#efe7d4; --ink:#2b2622; --muted:#6f665a;
  --rule:#d8cdb6; --accent:#8a6d3b; --card:#fbf7ec;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif;
  font-size:18px; line-height:1.65;
  background-image:radial-gradient(circle at 20% 0,rgba(255,255,255,.5),transparent 60%);
}
.wrap{max-width:720px; margin:0 auto; padding:40px 22px 80px}
header.site{border-bottom:1px solid var(--rule); padding-bottom:18px; margin-bottom:34px}
.brand{font-family:'Playfair Display',Georgia,serif; font-weight:700; font-size:30px; letter-spacing:.5px; text-decoration:none; color:var(--ink)}
.brand span{color:var(--accent)}
nav.top{margin-top:12px; font-size:15px}
nav.top a{color:var(--muted); text-decoration:none; margin-right:18px; border-bottom:1px solid transparent}
nav.top a:hover{color:var(--accent); border-bottom-color:var(--accent)}
h1{font-family:'Playfair Display',Georgia,serif; font-weight:700; font-size:34px; line-height:1.15; margin:0 0 6px}
h2{font-family:'Playfair Display',Georgia,serif; font-weight:700; font-size:22px; margin:38px 0 10px; color:var(--ink)}
.updated{color:var(--muted); font-size:15px; margin:0 0 8px}
p{margin:0 0 16px}
ul{margin:0 0 16px; padding-left:22px}
li{margin:0 0 8px}
a{color:var(--accent)}
strong{font-weight:700}
.card{background:var(--card); border:1px solid var(--rule); border-radius:14px; padding:22px 24px; margin:0 0 22px; box-shadow:0 1px 0 #fff inset}
.lede{font-size:20px; color:var(--muted); margin:0 0 26px}
footer.site{border-top:1px solid var(--rule); margin-top:56px; padding-top:20px; color:var(--muted); font-size:14px}
footer.site a{color:var(--muted)}
.btn{display:inline-block; background:var(--accent); color:#fff!important; text-decoration:none; padding:11px 20px; border-radius:10px; font-family:'Playfair Display',Georgia,serif; font-size:16px}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:15px}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&display=swap" rel="stylesheet">')


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
{FONTS}
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="site">
<a class="brand" href="index.html">Go<span>Be</span></a>
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
            out.append(f"<p>{inline(' '.join(para).strip())}</p>")
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
