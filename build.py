#!/usr/bin/env python3
"""Build GoBe's public legal/support site from the source markdown.

Run:  python3 build.py
Outputs: index.html, privacy.html, terms.html, support.html,
         assets/style.css, assets/grain.svg, .well-known/security.txt, .nojekyll

Security posture (static site, so hardened at the document level):
  - No third-party requests at all. Fonts (Cormorant Garamond) are self-hosted
    and subset; no Google Fonts, no CDN, no analytics — nothing that could leak a
    visitor's IP or inject code. Especially important on a Privacy Policy page.
  - Strict Content-Security-Policy meta: default-src 'none', only same-origin
    styles/fonts/images, no scripts, no framing of others, locked base-uri.
  - Referrer-Policy: no-referrer.
  - CSS is external (no inline <style>/style=) so the CSP needs no 'unsafe-inline'.
  - HTTPS is enforced at the GitHub Pages level (see repo Pages settings).

The privacy/terms pages are generated from the source markdown, kept word-for-word
in sync with the in-app Swift docs. Internal editor notes ('>' lines) are stripped.
Re-run after editing the .md files.
"""
import html
import re
from pathlib import Path

HERE = Path(__file__).parent
CONTACT = "hamedibakayoko82@gmail.com"
ORIGIN = "https://gobe-group.github.io"

# Content-Security-Policy — everything same-origin, no scripts, no third parties.
CSP = ("default-src 'none'; img-src 'self'; style-src 'self'; font-src 'self'; "
       "base-uri 'none'; form-action 'none'")

CSS = """
@font-face{font-family:'Cormorant Garamond';font-style:normal;font-weight:400;
  font-display:swap;src:url('fonts/cormorant-regular.woff') format('woff')}
@font-face{font-family:'Cormorant Garamond';font-style:normal;font-weight:700;
  font-display:swap;src:url('fonts/cormorant-bold.woff') format('woff')}

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
  --sans:'Avenir Next','Avenir','Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif;
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
  opacity:.035; mix-blend-mode:multiply; background-image:url('grain.svg');
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
nav.top a.active{color:var(--ink); border-bottom-color:var(--go-bright)}

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
.mono{font-family:var(--sans); font-size:15px; color:var(--ink-muted); letter-spacing:.3px}
.flush{margin:0}

/* ---------- Landing page ---------- */
.eyebrow{font-size:12px; font-weight:700; letter-spacing:1.6px; text-transform:uppercase; color:var(--go); margin:0 0 8px}
.wrap.home{max-width:940px}

.hero{display:grid; grid-template-columns:1fr minmax(220px,300px); gap:38px; align-items:center; margin:8px 0 20px}
.hero h1{font-size:clamp(38px,6vw,60px); margin:0 0 16px}
.hero p{font-size:20px; color:var(--ink-muted); line-height:1.5; margin:0 0 22px; max-width:36ch}
.hero-cta{display:flex; flex-wrap:wrap; gap:10px 22px; align-items:center}
.hero-cta.center{justify-content:center}
/* secondary text link next to a chunky button — quiet, on-brand, not a raw blue link */
.hero-cta a:not(.btn){color:var(--ink); font-weight:600; font-size:15px; text-decoration:none;
  border-bottom:2px solid var(--go-bright); padding-bottom:2px; transition:border-color .12s ease}
.hero-cta a:not(.btn):hover{border-bottom-color:var(--ink)}
.note{font-size:13px; color:var(--ink-muted); letter-spacing:.4px; margin:14px 0 0}

/* Phone screenshot as a hand-placed sticker card */
.shot{display:block; width:100%; height:auto; border-radius:26px;
  border:5px solid #fff; box-shadow:0 20px 40px rgba(43,36,29,.22), 0 0 0 1px var(--border-soft);
  background:#fff}
.hero .shot{transform:rotate(2deg)}

.features{display:grid; gap:30px; margin:56px 0 12px}
.feature{display:grid; grid-template-columns:minmax(220px,300px) 1fr; gap:36px; align-items:center;
  background:var(--paper-light); border:1px solid var(--border-soft); border-radius:26px; padding:28px;
  box-shadow:0 16px 34px rgba(43,36,29,.12), 0 2px 0 rgba(255,255,255,.55) inset}
.feature.rev{grid-template-columns:1fr minmax(220px,300px)}
.feature.rev .feat-media{order:2}
.feature h2{margin:0 0 12px; font-size:30px}
.feature p{margin:0; font-size:17px; line-height:1.55; color:var(--ink)}
.feature .shot{transform:rotate(-1.5deg)}
.feature.rev .shot{transform:rotate(1.5deg)}

.values{display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:48px 0 8px}
.value{background:#fff; border:1px solid var(--border-soft); border-radius:16px; padding:18px 16px;
  box-shadow:0 6px 14px var(--shadow)}
.value .vtitle{font-family:var(--serif); font-weight:700; font-size:22px; margin:0 0 4px}
.value p{margin:0; font-size:13.5px; color:var(--ink-muted); line-height:1.4}

.closer{text-align:center; margin:56px 0 8px}
.closer h2{font-size:34px; margin:0 0 10px}
.closer p{color:var(--ink-muted); font-size:18px; margin:0 auto 22px; max-width:44ch}

@media (max-width:720px){
  .hero{grid-template-columns:1fr; gap:26px}
  .hero .shot{max-width:280px; margin:0 auto}
  .feature,.feature.rev{grid-template-columns:1fr; gap:22px}
  .feature.rev .feat-media{order:0}
  .feature .shot{max-width:260px; margin:0 auto}
  .values{grid-template-columns:repeat(2,1fr)}
}
"""

GRAIN_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="140" height="140">'
             '<filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" '
             'numOctaves="2" stitchTiles="stitch"/></filter>'
             '<rect width="100%" height="100%" filter="url(#n)"/></svg>')


def page(title, body, active="", wrap_class=""):
    def nav(href, label):
        cls = ' class="active"' if active == href else ""
        return f'<a href="{href}"{cls}>{label}</a>'
    wrap = "wrap" + (f" {wrap_class}" if wrap_class else "")
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<meta name="referrer" content="no-referrer">
<title>{html.escape(title)} · GoBe</title>
<meta name="description" content="GoBe — leave and find traces of daily moments. {html.escape(title)}.">
<link rel="icon" type="image/png" href="assets/icon.png">
<link rel="apple-touch-icon" href="assets/icon.png">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<div class="{wrap}">
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
        stripped = raw.strip()
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


# --- Static assets ---
(HERE / "assets" / "style.css").write_text(CSS, encoding="utf-8")
(HERE / "assets" / "grain.svg").write_text(GRAIN_SVG, encoding="utf-8")
(HERE / ".nojekyll").write_text("", encoding="utf-8")  # serve dotfolders as-is
wk = HERE / ".well-known"
wk.mkdir(exist_ok=True)
(wk / "security.txt").write_text(
    f"Contact: mailto:{CONTACT}\n"
    f"Expires: 2027-07-08T00:00:00.000Z\n"
    f"Preferred-Languages: en\n"
    f"Canonical: {ORIGIN}/.well-known/security.txt\n"
    f"Policy: {ORIGIN}/privacy.html\n",
    encoding="utf-8",
)
print("wrote assets/style.css, assets/grain.svg, .well-known/security.txt, .nojekyll")

# --- Privacy & Terms (generated from markdown) ---
build_legal("gobe-privacy-policy.md", "Privacy Policy", "privacy.html", "privacy.html")
build_legal("gobe-terms-of-service.md", "Terms of Service", "terms.html", "terms.html")

# --- Support page ---
support = f"""<h1>Support</h1>
<p class="lede">Help with GoBe, and how to reach a real person.</p>
<div class="card">
<h2>Contact</h2>
<p>The fastest way to get help, report a problem, or ask a question is by email:</p>
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
home = f"""<section class="hero">
<div class="hero-copy">
<p class="eyebrow">Leave a trace · Go be there</p>
<h1>A little of your day, left where it happened.</h1>
<p>GoBe turns the places you go into a living map. Drop short notes and photos as
you move, and discover the traces other people have left behind, all around you.</p>
<div class="hero-cta">
<a class="btn" href="support.html">Get in touch</a>
<a href="privacy.html">Read our privacy promise &rsaquo;</a>
</div>
<p class="note">Made in the UK · For ages 16+ · Coming to the App Store</p>
</div>
<div class="hero-media">
<img class="shot" src="assets/screens/map.jpg" width="360" height="782"
  alt="The GoBe map of central London covered in traces left by people nearby">
</div>
</section>

<div class="features">

<div class="feature">
<div class="feat-media"><img class="shot" src="assets/screens/trace.jpg" width="300" height="652"
  alt="A GoBe trace card reading &quot;Great spot for watching the world go by&quot;"></div>
<div class="feat-copy">
<p class="eyebrow">Traces</p>
<h2>Read what others left behind.</h2>
<p>A Trace is a small thing someone noticed here — a note, a photo, a tip. Tap one
open to read it, like it, or retrace it onto your own map. Your neighbourhood, told
by the people who walk it.</p>
</div>
</div>

<div class="feature rev">
<div class="feat-media"><img class="shot" src="assets/screens/trail.jpg" width="300" height="652"
  alt="A finished GoBe trail along the South Bank with distance, time outside and a timeline of traces"></div>
<div class="feat-copy">
<p class="eyebrow">Trails</p>
<h2>Keep the path, not just the memory.</h2>
<p>Press play and GoBe quietly records the route you take. When you finish, you get a
keepsake of your day — the line you walked, how far you went, and every trace you
dropped along the way, in order.</p>
</div>
</div>

<div class="feature">
<div class="feat-media"><img class="shot" src="assets/screens/privacy.jpg" width="300" height="652"
  alt="GoBe's privacy screen for setting protected areas that are kept off the map"></div>
<div class="feat-copy">
<p class="eyebrow">Privacy first</p>
<h2>Your map, not your whereabouts.</h2>
<p>Traces are saved to an approximate spot — never your exact location. Mark protected
areas like home or work and GoBe keeps them off the map, stored only on your device.
No ads, and we never sell your data.</p>
</div>
</div>

</div>

<div class="values">
<div class="value"><div class="vtitle">No ads</div><p>Nothing following you around. GoBe is not built on attention.</p></div>
<div class="value"><div class="vtitle">Your data</div><p>We never sell it. Delete your account and content any time.</p></div>
<div class="value"><div class="vtitle">Made in the UK</div><p>A small, independent app, built with care in Britain.</p></div>
<div class="value"><div class="vtitle">Ages 16+</div><p>Higher-privacy defaults for younger users, by design.</p></div>
</div>

<div class="closer">
<h2>Go be somewhere.</h2>
<p>GoBe is on its way to the App Store. In the meantime, here's everything about how
it works and how we look after your data.</p>
<div class="hero-cta center">
<a class="btn" href="privacy.html">Privacy Policy</a>
<a class="btn" href="terms.html">Terms</a>
<a class="btn" href="support.html">Support</a>
</div>
</div>
"""
(HERE / "index.html").write_text(page("Home", home, "index.html", "home"), encoding="utf-8")
print("wrote index.html")
