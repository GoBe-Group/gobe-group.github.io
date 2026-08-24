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
import base64
import hashlib
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
CONTACT = "contact@gobeapp.co.uk"
ORIGIN = "https://gobeapp.co.uk"

# Universal-link identity. APP_ID is <App ID Prefix>.<bundle id> — the prefix is
# normally the Team ID (Xcode: DEVELOPMENT_TEAM on the GoBe target).
TEAM_ID = "DN2QB9489H"
BUNDLE_ID = "com.gobeapp.gobe"
APP_ID = f"{TEAM_ID}.{BUNDLE_ID}"

# Where someone without the app has to end up. The numeric id is what identifies
# the listing; the slug is cosmetic, but it's the one Apple prints on the listing
# so it's the one we use. The /gb/ storefront is not cosmetic: GoBe is only
# released in the UK, and the country-less form (apps.apple.com/app/id…) 404s
# for it, so the store link has to name the storefront it's actually in.
APP_STORE_ID = "6779702391"
APP_STORE_SLUG = "gobe-a-local-social-network"
APP_STORE_URL = f"https://apps.apple.com/gb/app/{APP_STORE_SLUG}/id{APP_STORE_ID}"
# The app's custom scheme, used to reach an installed GoBe from this page when
# iOS didn't hand the universal link over (in-app browsers strip them, and a
# "Safari" breadcrumb tap turns them off for the session).
APP_SCHEME = "gobe"

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
nav.top a{color:var(--ink-muted); text-decoration:none; margin-right:20px; padding-bottom:3px;
  border-bottom:2px solid transparent; display:inline-block; white-space:nowrap; line-height:2.1}
nav.top a:hover{color:var(--ink)}
nav.top a.active{color:var(--ink); border-bottom-color:var(--go-bright)}
/* the store link is the only outward one up here, so it carries GoBe blue */
nav.top a.get{color:var(--be); border-bottom-color:var(--be); margin-right:0}
nav.top a.get:hover{color:var(--be-dark); border-bottom-color:var(--be-dark)}

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
/* the one CTA that matters — same sticker, GoBe blue face, so it leads the row */
.btn.primary{background:var(--be); color:#fff!important; border-color:var(--be-dark);
  box-shadow:0 4px 0 var(--be-dark), 0 8px 14px var(--shadow)}
.btn.primary:active{box-shadow:0 1px 0 var(--be-dark), 0 3px 6px var(--shadow)}
.mono{font-family:var(--sans); font-size:15px; color:var(--ink-muted); letter-spacing:.3px}
.flush{margin:0}

/* ---------- Landing page ---------- */
/* The whole page argues one thing, in this order: what GoBe is, the three
   moves it is made of, what those moves add up to, and why that is not a feed.
   Every section below is one beat of that argument, so the markup reads in the
   same order somebody scrolling meets it. */
.eyebrow{font-size:12px; font-weight:700; letter-spacing:1.6px; text-transform:uppercase; color:var(--go); margin:0 0 8px}
.wrap.home{max-width:1040px}

/* Section heading with the paper rule under it, used to open each beat */
.beat{margin:74px 0 26px; max-width:52ch}
.beat.mid{margin-left:auto; margin-right:auto; text-align:center}
.beat h2{margin:0 0 10px; font-size:clamp(28px,3.8vw,38px)}
.beat p{margin:0; font-size:18px; color:var(--ink-muted); line-height:1.5}

.hero{display:grid; grid-template-columns:1fr minmax(230px,310px); gap:44px; align-items:center; margin:8px 0 20px}
.hero h1{font-size:clamp(38px,6vw,62px); margin:0 0 18px}
.hero p{font-size:20px; color:var(--ink-muted); line-height:1.5; margin:0 0 22px; max-width:40ch}
.hero-cta{display:flex; flex-wrap:wrap; gap:10px 22px; align-items:center}
.hero-cta.center{justify-content:center}
/* secondary text link next to a chunky button — quiet, on-brand, not a raw blue link */
.hero-cta a:not(.btn){color:var(--ink); font-weight:600; font-size:15px; text-decoration:none;
  border-bottom:2px solid var(--go-bright); padding-bottom:2px; transition:border-color .12s ease}
.hero-cta a:not(.btn):hover{border-bottom-color:var(--ink)}
.note{font-size:13px; color:var(--ink-muted); letter-spacing:.4px; margin:14px 0 0}
/* quiet links in a note line — underlined in GoBe green, never a raw blue link */
.note a{color:var(--ink); font-weight:600; text-decoration:none;
  border-bottom:2px solid var(--go-bright); padding-bottom:1px}

/* Phone screenshot as a hand-placed sticker card */
.shot{display:block; width:100%; height:auto; border-radius:26px;
  border:5px solid #fff; box-shadow:0 20px 40px rgba(43,36,29,.22), 0 0 0 1px var(--border-soft);
  background:#fff}
.hero .shot{transform:rotate(2deg)}

/* The sentence the rest of the page is an expansion of. Set big, on its own,
   so a visitor who reads nothing else still leaves knowing what GoBe is. */
.thesis{background:var(--paper-light); border:1px solid var(--border-soft); border-radius:30px;
  padding:44px 40px; margin:52px 0 0; text-align:center;
  box-shadow:0 16px 34px rgba(43,36,29,.12), 0 2px 0 rgba(255,255,255,.55) inset}
.thesis p:not(.eyebrow){font-family:var(--serif); font-size:clamp(24px,3.4vw,34px); line-height:1.26;
  margin:0 auto; max-width:27ch; color:var(--ink)}
.thesis .eyebrow{margin-bottom:16px}
.thesis em{font-style:normal; color:var(--go); }

/* The three moves, numbered, because the order is the product */
.steps{display:grid; grid-template-columns:repeat(3,1fr); gap:18px; margin:0 0 8px}
.step{background:var(--paper-light); border:1px solid var(--border-soft); border-radius:24px;
  padding:24px 22px 26px; box-shadow:0 12px 26px rgba(43,36,29,.11), 0 2px 0 rgba(255,255,255,.55) inset;
  display:flex; flex-direction:column}
.step .num{font-family:var(--serif); font-weight:700; font-size:22px; color:#fff;
  background:var(--go); width:38px; height:38px; border-radius:12px;
  display:flex; align-items:center; justify-content:center; margin:0 0 14px;
  box-shadow:0 3px 0 var(--cardboard-dark)}
.step h3{font-family:var(--serif); font-weight:700; font-size:25px; line-height:1.14; margin:0 0 9px}
.step p{margin:0; font-size:15.5px; line-height:1.5; color:var(--ink-muted)}
.step .word{color:var(--ink); font-weight:700}

/* Alternating screenshot / copy rows for the beats that need showing */
.split{display:grid; grid-template-columns:minmax(200px,262px) 1fr; gap:42px; align-items:center;
  background:var(--paper-light); border:1px solid var(--border-soft); border-radius:26px; padding:30px;
  box-shadow:0 16px 34px rgba(43,36,29,.12), 0 2px 0 rgba(255,255,255,.55) inset; margin:0 0 20px}
.split.rev{grid-template-columns:1fr minmax(200px,262px)}
.split.rev .split-media{order:2}
.split h3{font-family:var(--serif); font-weight:700; font-size:clamp(24px,3vw,31px); line-height:1.14; margin:0 0 12px}
.split p{margin:0 0 14px; font-size:17px; line-height:1.55; color:var(--ink)}
.split p:last-child{margin-bottom:0}
.split .shot{transform:rotate(-1.5deg)}
.split.rev .shot{transform:rotate(1.5deg)}
/* Two screenshots in one media slot, laid down like a pair of prints. The slot
   is widened to carry them, or each phone lands too small to read. */
.split.duo{grid-template-columns:minmax(240px,346px) 1fr}
.split.duo.rev{grid-template-columns:1fr minmax(240px,346px)}
.pair{display:grid; grid-template-columns:1fr 1fr; gap:12px; align-items:start}
.pair .shot{border-width:4px; border-radius:20px}
.pair .shot:first-child{transform:rotate(-2deg)}
.pair .shot:last-child{transform:rotate(2deg); margin-top:16px}

/* A screen that is wider than it is tall, so it gets a landscape slot rather
   than being squeezed into the portrait phone shape the other shots use. */
.wide{display:grid; grid-template-columns:minmax(0,1.05fr) minmax(0,1fr); gap:38px; align-items:center;
  background:var(--paper-light); border:1px solid var(--border-soft); border-radius:26px; padding:30px;
  box-shadow:0 16px 34px rgba(43,36,29,.12), 0 2px 0 rgba(255,255,255,.55) inset; margin:0}
.wide .shot{transform:rotate(-1deg)}
.wide-copy p:not(.eyebrow){margin:0; font-size:17px; line-height:1.55; color:var(--ink)}

/* Feed on the left, GoBe on the right. The clearest way to say what this is
   instead of describing it twice. */
.contrast{display:grid; grid-template-columns:1fr 1fr; gap:0; margin:0;
  border:1px solid var(--border-soft); border-radius:26px; overflow:hidden;
  box-shadow:0 16px 34px rgba(43,36,29,.12)}
.col{padding:26px 26px 30px}
.col.was{background:var(--paper-aged)}
.col.is{background:#fff}
.col h3{font-family:var(--serif); font-weight:700; font-size:24px; margin:0 0 4px}
.col .ceyebrow{font-size:11.5px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase;
  color:var(--ink-muted); margin:0 0 12px}
.col.is .ceyebrow{color:var(--go)}
.col ul{list-style:none; margin:0; padding:0}
.col li{margin:0 0 11px; font-size:15.5px; line-height:1.45; padding-left:20px; position:relative}
.col li::before{content:""; position:absolute; left:0; top:.62em; width:9px; height:2px; background:var(--cardboard)}
.col.is li::before{background:var(--go-bright); height:3px}
.col.was li{color:var(--ink-muted)}

.values{display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:24px 0 8px}
.value{background:#fff; border:1px solid var(--border-soft); border-radius:16px; padding:18px 16px;
  box-shadow:0 6px 14px var(--shadow)}
.value .vtitle{font-family:var(--serif); font-weight:700; font-size:22px; margin:0 0 4px}
.value p{margin:0; font-size:13.5px; color:var(--ink-muted); line-height:1.4}

/* The band for people reading this as a business rather than an app */
.brief{background:var(--paper-light); border:1px solid var(--border-soft); border-radius:26px;
  padding:32px 30px; margin:0;
  box-shadow:0 16px 34px rgba(43,36,29,.12), 0 2px 0 rgba(255,255,255,.55) inset}
.brief h3{font-family:var(--serif); font-weight:700; font-size:28px; margin:0 0 10px}
.brief p{font-size:17px; line-height:1.55; margin:0 0 16px}
.facts{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px 26px; margin:20px 0 0;
  border-top:1px solid var(--border-soft); padding-top:20px}
.fact{display:flex; gap:12px; font-size:15px; line-height:1.4}
.fact .k{font-size:11.5px; font-weight:700; letter-spacing:1.4px; text-transform:uppercase;
  color:var(--ink-muted); min-width:112px; padding-top:3px}
.fact .v{color:var(--ink)}
/* the contact line sits under the facts, not in them, so it needs its own air */
.brief .note{margin-top:22px}

/* ---------- Profile handoff (/u/) ---------- */
/* The page a shared profile link lands on when GoBe isn't installed to catch it.
   Deliberately shows no profile data — just the handoff. */
.handoff{text-align:center; margin:26px 0 8px}
.handoff h1{font-size:clamp(32px,5.4vw,46px); margin:0 0 14px}
.handoff .lede{max-width:40ch; margin:0 auto 26px}
.handoff .hero-cta{justify-content:center}
/* Die-cut sticker window holding the app mark, same language as the app's share artefact */
.handoff-mark{display:inline-block; background:#fff; border:5px solid #fff; border-radius:24px;
  box-shadow:0 16px 34px rgba(43,36,29,.2), 0 0 0 1px var(--border-soft);
  transform:rotate(-2deg); margin:0 0 26px; line-height:0}
.handoff-mark img{width:96px; height:96px; border-radius:20px; display:block}

.closer{text-align:center; margin:56px 0 8px}
.closer h2{font-size:34px; margin:0 0 10px}
.closer p{color:var(--ink-muted); font-size:18px; margin:0 auto 22px; max-width:44ch}

@media (max-width:860px){
  .steps{grid-template-columns:1fr}
  .step{padding:20px 20px 22px}
}
@media (max-width:720px){
  .wrap{padding:30px 18px 64px}
  .hero{grid-template-columns:1fr; gap:26px}
  .hero .shot{max-width:280px; margin:0 auto}
  .beat{margin:52px 0 20px}
  .thesis{padding:32px 22px}
  /* .duo carries a wider media slot, and a higher specificity with it, so the
     stack has to name it or the two-print rows never collapse. */
  .split,.split.rev,.split.duo,.split.duo.rev{grid-template-columns:1fr; gap:22px}
  .split.rev .split-media{order:0}
  .split .shot{max-width:260px; margin:0 auto}
  .pair{max-width:340px; margin:0 auto}
  .wide{grid-template-columns:1fr; gap:22px}
  .contrast{grid-template-columns:1fr}
  .values{grid-template-columns:repeat(2,1fr)}
  .facts{grid-template-columns:1fr}
  .fact{flex-direction:column; gap:2px}
}
"""

GRAIN_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="140" height="140">'
             '<filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" '
             'numOctaves="2" stitchTiles="stitch"/></filter>'
             '<rect width="100%" height="100%" filter="url(#n)"/></svg>')


def page(title, body, active="", wrap_class="", base="", description="", csp=CSP, head=""):
    """Render a full page. `base` prefixes every internal link — pass "/" for
    pages that don't live at the site root (e.g. /u/), so assets still resolve.

    `csp` and `head` exist for the one page that needs a script (/u/, which has
    to reach an installed app); every other page keeps the script-free default."""
    def nav(href, label):
        cls = ' class="active"' if active == href else ""
        return f'<a href="{base}{href}"{cls}>{label}</a>'
    wrap = "wrap" + (f" {wrap_class}" if wrap_class else "")
    desc = description or f"GoBe — leave and find traces of daily moments. {title}."
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<meta name="referrer" content="no-referrer">
<title>{html.escape(title)} · GoBe</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:site_name" content="GoBe">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(title)} · GoBe">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:image" content="{ORIGIN}/assets/icon.png">
<meta name="twitter:card" content="summary">
<link rel="icon" type="image/png" href="{base}assets/icon.png">
<link rel="apple-touch-icon" href="{base}assets/icon.png">
<link rel="stylesheet" href="{base}assets/style.css">
{head}</head>
<body>
<div class="{wrap}">
<header class="site">
<a class="brand" href="{base}index.html"><img src="{base}assets/gobe-logo.png" alt="GoBe" width="140" height="56"></a>
<nav class="top">{nav('index.html','Home')}{nav('index.html#how','How it works')}{nav('privacy.html','Privacy')}{nav('terms.html','Terms')}{nav('support.html','Support')}<a class="get" href="{APP_STORE_URL}">Get the app</a></nav>
</header>
{body}
<footer class="site">
<p>GoBe is operated by Hamed Bakayoko, sole trader trading as GoBe, 124 City Road, London EC1V 2NX, United Kingdom.<br>
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

# apple-app-site-association — lets iOS hand /u/ links straight to the GoBe app
# instead of opening Safari. Must be served at this exact path, with no file
# extension, over HTTPS, with no redirect. `.nojekyll` above is what stops
# GitHub Pages hiding the dot-directory.
(wk / "apple-app-site-association").write_text(
    json.dumps(
        {
            "applinks": {
                "details": [
                    {
                        "appIDs": [APP_ID],
                        # Both forms: "/u/" is the link we actually share
                        # (the handle rides in ?h=), "/u/*" covers the older
                        # pretty-path links that are still out there.
                        "components": [
                            {"/": "/u/", "comment": "profile links"},
                            {"/": "/u/*", "comment": "profile links (path form)"},
                            {"/": "/g/", "comment": "gathering links"},
                            {"/": "/g/*", "comment": "gathering links (path form)"},
                            {"/": "/i/", "comment": "invite links"},
                            {"/": "/i/*", "comment": "invite links (path form)"},
                        ],
                    }
                ]
            }
        },
        indent=2,
    ),
    encoding="utf-8",
)
# Apple requires the association file to be served as application/json. GitHub
# Pages sends application/octet-stream for extensionless files and gives no way
# to change it, which is what has kept universal links from working. Hosts that
# read a `_headers` file (Cloudflare Pages, Netlify) honour this; on GitHub Pages
# it's simply an inert text file, so it's safe to ship either way.
(HERE / "_headers").write_text(
    "/.well-known/apple-app-site-association\n"
    "  Content-Type: application/json\n"
    "  Cache-Control: public, max-age=3600\n",
    encoding="utf-8",
)
print("wrote assets/style.css, assets/grain.svg, .well-known/security.txt,"
      " .well-known/apple-app-site-association, .nojekyll, _headers")

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
# The page makes one argument, in this order: what GoBe is, the three moves it
# is made of, what those moves add up to, why that is not a feed, and how it
# stays safe. Anyone who reads only the hero and the line under it should still
# be able to say what the app does, which is the test this page has to pass.
HOME_TITLE = "A social network on a map, not in a feed"
HOME_DESC = (
    "GoBe is a social network for meeting people and enjoying experiences local to you, "
    "offline. Record your journeys as trails, leave location-pinned posts called traces, "
    "and find the people whose lives cross the same streets."
)

home = f"""<section class="hero">
<div class="hero-copy">
<p class="eyebrow">A local social network</p>
<h1>The social network on a map, not in a feed.</h1>
<p>GoBe helps you meet people and enjoy experiences local to you, offline. People record
their everyday journeys as <strong>trails</strong> and leave location-pinned posts, called
<strong>traces</strong>, for others to discover where they were created.</p>
<div class="hero-cta">
<a class="btn primary" href="{APP_STORE_URL}">Download on the App Store</a>
<a href="#how">See how it works &rsaquo;</a>
</div>
<p class="note">Free for iPhone · Made in the UK · For ages 16+</p>
</div>
<div class="hero-media">
<img class="shot" src="assets/screens/map.jpg" width="720" height="1565"
  alt="The GoBe map of central London, covered in traces left by people nearby">
</div>
</section>

<div class="thesis">
<p class="eyebrow">The whole idea</p>
<p>As trails overlap, GoBe reveals the people whose lives <em>cross the same streets</em>.</p>
</div>

<div class="beat mid" id="how">
<h2>Three moves, and that is the whole app.</h2>
<p>No ranking, no recommendations, no infinite scroll. Where you went, what you left,
and who else has been there.</p>
</div>

<div class="steps">
<div class="step">
<div class="num">1</div>
<h3>Walk your day</h3>
<p>Press play and GoBe quietly records the route you take as a <span class="word">trail</span>.
When you finish you keep the line you walked, how far you went and how long you were outside.</p>
</div>
<div class="step">
<div class="num">2</div>
<h3>Leave a trace</h3>
<p>A <span class="word">trace</span> is a post pinned to the spot it belongs to: a note, a photo,
a video, or nothing at all. An empty trace still says the truest thing there is, that you were here.</p>
</div>
<div class="step">
<div class="num">3</div>
<h3>Be found there</h3>
<p>Traces stay where they were made. They are read by whoever gets to that spot, which means
the only way to reach one another is to actually <span class="word">turn up</span>.</p>
</div>
</div>

<div class="beat">
<h2>Your day, kept as a line on the map.</h2>
<p>A trail is a record of somewhere you actually went, not a post about it. Trails are
private to you by default, and what they are for is what happens when they overlap.</p>
</div>

<div class="split duo">
<div class="split-media"><div class="pair">
<img class="shot" src="assets/screens/recording.jpg" width="720" height="1565" loading="lazy"
  alt="A GoBe trail being recorded along Whitehall, the walked route drawn in green behind the walker">
<img class="shot" src="assets/screens/trail.jpg" width="720" height="1565" loading="lazy"
  alt="A finished GoBe trail along the South Bank, with distance travelled, time outside and a timeline of the traces left along the way">
</div></div>
<div class="split-copy">
<p class="eyebrow">Trails</p>
<h3>Recorded while you walk, kept when you stop.</h3>
<p>GoBe follows the route in the background while a trail is running, up to twelve hours,
and stops the moment you finish. What you get back is a keepsake of the day: the shape of
the walk, the distance, the time you spent outside and every trace you left, in order.</p>
<p>Turn location off part way through and the trail is discarded rather than half kept.
It is a record of a real journey or it is nothing.</p>
</div>
</div>

<div class="split duo rev">
<div class="split-media"><div class="pair">
<img class="shot" src="assets/screens/trace.jpg" width="720" height="1565" loading="lazy"
  alt="A GoBe trace opened on the map, reading &quot;Great spot for watching the world go by&quot;, with its author, likes and retraces">
<img class="shot" src="assets/screens/compose.jpg" width="720" height="1565" loading="lazy"
  alt="Leaving a trace in GoBe, a note being written on a paper card pinned to the spot on the map">
</div></div>
<div class="split-copy">
<p class="eyebrow">Traces</p>
<h3>Something small, left where it happened.</h3>
<p>Tap a trace to read it, like it, or retrace it onto your own map. Reach one in person and
you can <strong>pass</strong> it, which records that you made it to the same place rather than
posting a copy of somebody else's moment.</p>
<p>Your neighbourhood, described by the people who walk it, in the spots they were describing.</p>
</div>
</div>

<div class="beat">
<h2>Then the map starts introducing you.</h2>
<p>This is the part a feed cannot do. Geography, not an algorithm, decides who you meet.</p>
</div>

<div class="split">
<div class="split-media">
<img class="shot" src="assets/screens/places.jpg" width="720" height="1565" loading="lazy"
  alt="The GoBe map showing the traces sitting around the reader: a cafe window, a park path, a bookshop, a sunset spot and somewhere to have lunch">
</div>
<div class="split-copy">
<p class="eyebrow">People, places, communities</p>
<h3>The people whose lives cross the same streets.</h3>
<p>Everyone whose traces are within reach of you is somebody who has been standing where you
are standing. GoBe can also notice when another person has walked a street you walked, and
tell you both, if you have each chosen to be told.</p>
<p>Alongside them sits what is actually around you: places to eat, drink, read, train, shop
and do something, so the map answers the ordinary question of what to do this afternoon as
well as the bigger one of who is out there.</p>
</div>
</div>

<div class="beat">
<h2>Every trace adds up to somewhere.</h2>
<p>A trail travelled and a trace left are not just yours. They are a contribution to the life
of a neighbourhood, a borough and a city, which is the reason to keep participating in the
place you already live.</p>
</div>

<div class="wide">
<img class="shot" src="assets/screens/areas.jpg" width="720" height="836" loading="lazy"
  alt="GoBe's areas screen, showing the reader standing second of forty-seven in Mitcham and fifth of a hundred and thirty-two in Merton">
<div class="wide-copy">
<p class="eyebrow">Neighbourhood, borough, city</p>
<p>The same walking, counted at every scale it belongs to. Not a score for its own sake:
a way of showing that turning up in your own area is worth something, and that the map of
a place is built by the people who live in it.</p>
</div>
</div>

<div class="contrast">
<div class="col was">
<p class="ceyebrow">A feed</p>
<h3>Rewards attention</h3>
<ul>
<li>Ranked by an algorithm optimising for time spent</li>
<li>Everybody's content, from everywhere, all at once</li>
<li>The best outcome is that you keep scrolling</li>
<li>Ends on the screen</li>
</ul>
</div>
<div class="col is">
<p class="ceyebrow">GoBe</p>
<h3>Rewards turning up</h3>
<ul>
<li>Arranged by geography, so distance decides what you see</li>
<li>What was left here, found by whoever gets here</li>
<li>The best outcome is that you go somewhere</li>
<li>Ends outside, in your own area, with people from it</li>
</ul>
</div>
</div>

<div class="beat">
<h2>Built so that being outside stays safe.</h2>
<p>A social network made of real places only works if it never becomes a way to find a
person at one.</p>
</div>

<div class="split rev">
<div class="split-media">
<img class="shot" src="assets/screens/privacy.jpg" width="720" height="1565" loading="lazy"
  alt="GoBe's privacy screen, where protected areas such as home or work are set and kept off the map">
</div>
<div class="split-copy">
<p class="eyebrow">Privacy</p>
<h3>Your map, not your whereabouts.</h3>
<p>Traces are saved to an approximate spot, rounded to a grid roughly thirty metres across,
and the exact coordinate is never stored, on your device or on our servers. The route of a
trail is more detailed, and that is exactly why a trail stays private to you.</p>
<p>Mark protected areas such as home or work and GoBe refuses to place a trace inside them.
Those areas are kept on your device only. No ads, and we never sell your data.</p>
</div>
</div>

<div class="values">
<div class="value"><div class="vtitle">No ads</div><p>Nothing following you around. GoBe is not built on attention.</p></div>
<div class="value"><div class="vtitle">Your data</div><p>We never sell it. Delete your account and content any time.</p></div>
<div class="value"><div class="vtitle">Made in the UK</div><p>A small, independent app, built with care in Britain.</p></div>
<div class="value"><div class="vtitle">Ages 16+</div><p>Higher-privacy defaults for younger users, by design.</p></div>
</div>

<div class="beat" id="about">
<h2>Reading this as a business?</h2>
</div>

<div class="brief">
<h3>The short version.</h3>
<p>Social networks have spent fifteen years getting better at holding people in a feed and
worse at getting them into a room. GoBe puts the network back on the ground: the unit of
content is a place you stood in, the unit of distribution is how near you are to it, and the
success condition is that somebody leaves the house.</p>
<p>That geography is also the moat. A map filled in by the people who walk a neighbourhood
cannot be bought or scraped into existence somewhere else, and it gets more useful to
everybody in that neighbourhood with each trace left in it. GoBe grows the way a place does,
street by street, rather than all at once and everywhere.</p>
<div class="facts">
<div class="fact"><div class="k">Status</div><div class="v">Live on the App Store, free, iPhone</div></div>
<div class="fact"><div class="k">Category</div><div class="v">Social networking, location first</div></div>
<div class="fact"><div class="k">Availability</div><div class="v">United Kingdom, English (U.K.)</div></div>
<div class="fact"><div class="k">Audience</div><div class="v">Ages 16 and over</div></div>
<div class="fact"><div class="k">Business model</div><div class="v">No advertising, and no sale of user data</div></div>
<div class="fact"><div class="k">Operator</div><div class="v">Independent, UK sole trader, London</div></div>
</div>
<p class="note">Investors, partners and press: <a href="mailto:{CONTACT}">{CONTACT}</a></p>
</div>

<div class="closer">
<h2>Go be somewhere.</h2>
<p>GoBe is free on the App Store, for iPhone. Here is everything about how it works and how
we look after your data.</p>
<div class="hero-cta center">
<a class="btn primary" href="{APP_STORE_URL}">Download on the App Store</a>
<a class="btn" href="privacy.html">Privacy Policy</a>
<a class="btn" href="terms.html">Terms</a>
<a class="btn" href="support.html">Support</a>
</div>
</div>
"""
(HERE / "index.html").write_text(
    page(HOME_TITLE, home, "index.html", "home", description=HOME_DESC),
    encoding="utf-8",
)
print("wrote index.html")

# --- Profile handoff (/u/) ---
# Where a shared profile link lands when iOS didn't hand it to the app. Ideally
# it never loads at all: the apple-app-site-association above claims /u/, so on a
# device with GoBe the universal link opens the app directly. It loads when the
# app isn't installed, when the link was tapped inside an in-app browser
# (Instagram, WhatsApp and friends strip universal links), or after someone taps
# the "Safari" breadcrumb, which switches universal links off for that site.
#
# So the page has exactly two jobs, and it now does both rather than telling
# people to "tap the link again":
#   1. Installed? Reach the app over the gobe:// scheme, handle and all.
#   2. Not installed? Land on the App Store product page.
# Both are attempted in that order: fire the scheme, and if we're still here a
# beat later, the app isn't there to take it, so go to the App Store.
#
# It still shows NO profile data — not the name, avatar, or traces. Profiles in
# GoBe are behind sign-in and bond-gated, and a public web page would quietly
# undo that. The handle sits in the URL, is passed to the app, and is never
# rendered here.
#
# The one script on the whole site lives here, because only JavaScript can read
# ?h= out of the URL and time the fallback. It is inline and pinned by a
# sha256 CSP hash computed below, so the page still loads nothing external and
# no other script can run on it. Without JavaScript, both buttons are plain
# links to the App Store, which is the right destination for anyone who can't
# be handed to the app.
HANDOFF_JS = f"""(function(){{
  var STORE = {json.dumps(APP_STORE_URL)};
  var q = new URLSearchParams(location.search);
  // Accept both link shapes: /u/?h=ada (what we share) and /u/ada (older links).
  var raw = q.get('h');
  if (!raw) {{
    try {{ raw = decodeURIComponent(location.pathname.replace(/^\\/u\\/?/, '')); }}
    catch (e) {{ raw = ''; }}
  }}
  var handle = (raw || '').trim().replace(/^@/, '').replace(/\\/+$/, '');
  // Only ever hand the app a plain handle, so nothing from the URL can steer
  // the scheme link somewhere else.
  var ok = /^[A-Za-z0-9._-]{{1,40}}$/.test(handle);
  var appURL = ok ? '{APP_SCHEME}://u/?h=' + encodeURIComponent(handle) : null;
  var iOS = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
            (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

  // Try the app, then the App Store. The timer is cancelled if the page gets
  // hidden or unloaded, which is what happens the instant iOS switches to GoBe,
  // so someone who has the app never gets bounced to the store behind it.
  function reach(event) {{
    if (!appURL) return;             // no handle: the button is already the store
    if (event) event.preventDefault();
    var timer = setTimeout(function () {{
      if (document.visibilityState !== 'hidden') location.replace(STORE);
    }}, 1400);
    function cancel() {{ clearTimeout(timer); }}
    document.addEventListener('visibilitychange', function () {{
      if (document.hidden) cancel();
    }});
    window.addEventListener('pagehide', cancel);
    location.href = appURL;
  }}

  // This runs in <head>, so wait for the button to exist before wiring it.
  function start() {{
    var openBtn = document.getElementById('open-in-app');
    if (openBtn) {{
      if (appURL) openBtn.href = appURL;
      openBtn.addEventListener('click', reach);
    }}
    // On an iPhone the whole point of the link is to land in the app, so don't
    // wait for a second tap. Elsewhere (desktop, Android) there's no app to
    // reach, so the page just explains itself and offers the App Store.
    // ?noauto=1 turns the automatic attempt off, for looking at this page.
    if (iOS && appURL && !q.has('noauto')) reach();
  }}

  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', start);
  }} else {{
    start();
  }}
}})();"""

HANDOFF_CSP = (
    "default-src 'none'; img-src 'self'; style-src 'self'; font-src 'self'; "
    "script-src 'sha256-{hash}'; base-uri 'none'; form-action 'none'"
).format(hash=base64.b64encode(hashlib.sha256(HANDOFF_JS.encode("utf-8")).digest()).decode())

profile = f"""<section class="handoff">
<div class="handoff-mark"><img src="/assets/icon.png" alt="" width="96" height="96"></div>
<p class="eyebrow">Someone shared their GoBe</p>
<h1>Open this profile in GoBe.</h1>
<p class="lede">Profile links open straight in the app. If GoBe isn't on this
iPhone yet, you'll be taken to the App Store to get it.</p>
<div class="hero-cta">
<a class="btn" id="open-in-app" href="{APP_STORE_URL}">Open in GoBe</a>
<a class="btn" href="{APP_STORE_URL}">Get GoBe</a>
</div>
<p class="note">Free on the App Store · Made in the UK · For ages 16+</p>
<p class="note"><a href="/index.html">What is GoBe?</a> · <a href="/support.html">Need a hand?</a></p>
</section>

<div class="card">
<h2>Why can't I see the profile here?</h2>
<p>GoBe profiles aren't public web pages. What someone has posted is visible inside
the app, to people they've added, not to anyone holding a link. So this page hands
you over to the app rather than showing you their traces.</p>
<p class="flush">More on how we handle your data in our
<a href="/privacy.html">Privacy Policy</a>.</p>
</div>
"""
(HERE / "u").mkdir(exist_ok=True)
(HERE / "u" / "index.html").write_text(
    page(
        "Profile",
        profile,
        base="/",
        description="Open this GoBe profile in the app. GoBe — leave and find traces of daily moments.",
        csp=HANDOFF_CSP,
        head=f"<script>{HANDOFF_JS}</script>\n",
    ),
    encoding="utf-8",
)
print("wrote u/index.html")

# --- /g/ : a shared community or event -------------------------------------
#
# The same two jobs as /u/, and the same refusal to show anything: installed,
# reach the app over gobe://; not installed, land on the App Store. A gathering
# has a name, a blurb and a place, and none of them is rendered here — a link is
# forwardable and a web page is public, so publishing what a gathering is would
# quietly hand strangers the thing the app only shows to people who joined.
#
# The id is a UUID rather than a name, because two running clubs in two cities
# can both be called "Tuesday runners" and a link that opens the wrong one is
# worse than a link that is ugly. It is validated as a UUID before it is handed
# anywhere, so nothing from the URL can steer the scheme link.
GATHERING_JS = f"""(function(){{
  var STORE = {json.dumps(APP_STORE_URL)};
  var q = new URLSearchParams(location.search);
  // Accept both shapes: /g/?id=<uuid> (what we share) and /g/<uuid>.
  var raw = q.get('id');
  if (!raw) {{
    try {{ raw = decodeURIComponent(location.pathname.replace(/^\\/g\\/?/, '')); }}
    catch (e) {{ raw = ''; }}
  }}
  var id = (raw || '').trim().replace(/\\/+$/, '').toLowerCase();
  var ok = /^[0-9a-f]{{8}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{12}}$/.test(id);
  var appURL = ok ? '{APP_SCHEME}://g/?id=' + encodeURIComponent(id) : null;
  var iOS = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
            (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

  function reach(event) {{
    if (!appURL) return;
    if (event) event.preventDefault();
    var timer = setTimeout(function () {{
      if (document.visibilityState !== 'hidden') location.replace(STORE);
    }}, 1400);
    function cancel() {{ clearTimeout(timer); }}
    document.addEventListener('visibilitychange', function () {{
      if (document.hidden) cancel();
    }});
    window.addEventListener('pagehide', cancel);
    location.href = appURL;
  }}

  function start() {{
    var openBtn = document.getElementById('open-in-app');
    if (openBtn) {{
      if (appURL) openBtn.href = appURL;
      openBtn.addEventListener('click', reach);
    }}
    if (iOS && appURL && !q.has('noauto')) reach();
  }}

  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', start);
  }} else {{
    start();
  }}
}})();"""

GATHERING_CSP = (
    "default-src 'none'; img-src 'self'; style-src 'self'; font-src 'self'; "
    "script-src 'sha256-{hash}'; base-uri 'none'; form-action 'none'"
).format(hash=base64.b64encode(hashlib.sha256(GATHERING_JS.encode("utf-8")).digest()).decode())

gathering = f"""<section class="handoff">
<div class="handoff-mark"><img src="/assets/icon.png" alt="" width="96" height="96"></div>
<p class="eyebrow">Someone shared a gathering</p>
<h1>Open this in GoBe.</h1>
<p class="lede">Community and event links open straight in the app. If GoBe isn't
on this iPhone yet, you'll be taken to the App Store to get it.</p>
<div class="hero-cta">
<a class="btn" id="open-in-app" href="{APP_STORE_URL}">Open in GoBe</a>
<a class="btn" href="{APP_STORE_URL}">Get GoBe</a>
</div>
<p class="note">Free on the App Store · Made in the UK · For ages 16+</p>
<p class="note"><a href="/index.html">What is GoBe?</a> · <a href="/support.html">Need a hand?</a></p>
</section>

<div class="card">
<h2>What is this?</h2>
<p>A <strong>community</strong> is a standing group pinned to a place on the map.
An <strong>event</strong> is the same thing with a date on it. People join them,
and a trace left to one can be opened by everyone who joined, from anywhere.</p>
<h2>Why can't I see it here?</h2>
<p>Gatherings aren't public web pages. What has been left to one is visible inside
the app, to the people who joined it, not to anyone holding a link. So this page
hands you over to the app rather than showing you what's there.</p>
<p class="flush">More on how we handle your data in our
<a href="/privacy.html">Privacy Policy</a>.</p>
</div>
"""
(HERE / "g").mkdir(exist_ok=True)
(HERE / "g" / "index.html").write_text(
    page(
        "Gathering",
        gathering,
        base="/",
        description="Open this GoBe community or event in the app. GoBe — leave and find traces of daily moments.",
        csp=GATHERING_CSP,
        head=f"<script>{GATHERING_JS}</script>\n",
    ),
    encoding="utf-8",
)
print("wrote g/index.html")

# --- /i/ : an invitation to a gathering -------------------------------------
#
# The same handoff as /g/, and one important difference: the thing in the URL is
# a secret rather than an identifier. Opening this link inside the app spends it
# and puts the holder into the gathering, so this page is careful in two ways
# /g/ does not have to be.
#
# It renders nothing about the invitation — not the gathering, not who sent it,
# not the token — and it sets no referrer, so the secret cannot leak sideways
# into an analytics request or a referer header on the way to the App Store.
# (`meta name="referrer" content="no-referrer"` is already on every page here.)
#
# The token is validated as URL-safe base64 before it is handed anywhere, so
# nothing from the URL can steer the scheme link.
INVITE_JS = f"""(function(){{
  var STORE = {json.dumps(APP_STORE_URL)};
  var q = new URLSearchParams(location.search);
  // Accept both shapes: /i/?t=<token> (what we send) and /i/<token>.
  var raw = q.get('t');
  if (!raw) {{
    try {{ raw = decodeURIComponent(location.pathname.replace(/^\\/i\\/?/, '')); }}
    catch (e) {{ raw = ''; }}
  }}
  var token = (raw || '').trim().replace(/\\/+$/, '');
  var ok = /^[A-Za-z0-9_-]{{16,128}}$/.test(token);
  var appURL = ok ? '{APP_SCHEME}://i/?t=' + encodeURIComponent(token) : null;
  var iOS = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
            (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

  function reach(event) {{
    if (!appURL) return;
    if (event) event.preventDefault();
    var timer = setTimeout(function () {{
      if (document.visibilityState !== 'hidden') location.replace(STORE);
    }}, 1400);
    function cancel() {{ clearTimeout(timer); }}
    document.addEventListener('visibilitychange', function () {{
      if (document.hidden) cancel();
    }});
    window.addEventListener('pagehide', cancel);
    location.href = appURL;
  }}

  function start() {{
    var openBtn = document.getElementById('open-in-app');
    if (openBtn) {{
      if (appURL) openBtn.href = appURL;
      openBtn.addEventListener('click', reach);
    }}
    if (iOS && appURL && !q.has('noauto')) reach();
  }}

  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', start);
  }} else {{
    start();
  }}
}})();"""

INVITE_CSP = (
    "default-src 'none'; img-src 'self'; style-src 'self'; font-src 'self'; "
    "script-src 'sha256-{hash}'; base-uri 'none'; form-action 'none'"
).format(hash=base64.b64encode(hashlib.sha256(INVITE_JS.encode("utf-8")).digest()).decode())

invite = f"""<section class="handoff">
<div class="handoff-mark"><img src="/assets/icon.png" alt="" width="96" height="96"></div>
<p class="eyebrow">You have been invited</p>
<h1>Open this in GoBe.</h1>
<p class="lede">An invite link opens straight in the app and takes you into the
community or event that sent it. If GoBe isn't on this iPhone yet, you'll be
taken to the App Store to get it.</p>
<div class="hero-cta">
<a class="btn" id="open-in-app" href="{APP_STORE_URL}">Open in GoBe</a>
<a class="btn" href="{APP_STORE_URL}">Get GoBe</a>
</div>
<p class="note">Free on the App Store · Made in the UK · For ages 16+</p>
<p class="note"><a href="/index.html">What is GoBe?</a> · <a href="/support.html">Need a hand?</a></p>
</section>

<div class="card">
<h2>What is this?</h2>
<p>Somebody in a GoBe <strong>community</strong> or <strong>event</strong> sent
you a way in. Opening the link in the app joins you to it, without waiting for
anyone to approve you.</p>
<h2>Why can't I see it here?</h2>
<p>This page shows nothing about the invitation on purpose. A link can be
forwarded and a web page is public, so naming the gathering here would hand it
to anyone the link reached. It also means an invite that has been withdrawn
looks exactly like one that was never real, which is the point.</p>
<p class="flush">More on how we handle your data in our
<a href="/privacy.html">Privacy Policy</a>.</p>
</div>
"""
(HERE / "i").mkdir(exist_ok=True)
(HERE / "i" / "index.html").write_text(
    page(
        "Invite",
        invite,
        base="/",
        description="Open your GoBe invite in the app. GoBe — leave and find traces of daily moments.",
        csp=INVITE_CSP,
        head=f"<script>{INVITE_JS}</script>\n",
    ),
    encoding="utf-8",
)
print("wrote i/index.html")

# --- 404 ---
# The site is a set of real files, so the pretty profile form (/u/ada) has no
# file behind it and 404s. That form predates the ?h= query and is still out
# there in already-sent messages, and the app happily parses it, so a visitor
# without the app shouldn't hit a dead end. This page sends those straight to
# the canonical /u/?h= handoff, which then does the app-then-App-Store dance.
# Everything else gets an ordinary, on-brand "not found".
NOT_FOUND_JS = """(function(){
  var u = location.pathname.match(/^\\/u\\/([^\\/?#]+)\\/?$/);
  if (u) {
    var handle = decodeURIComponent(u[1]).trim().replace(/^@/, '');
    if (!/^[A-Za-z0-9._-]{1,40}$/.test(handle)) return;
    location.replace('/u/?h=' + encodeURIComponent(handle));
    return;
  }
  var g = location.pathname.match(/^\\/g\\/([^\\/?#]+)\\/?$/);
  if (g) {
    var id = decodeURIComponent(g[1]).trim().toLowerCase();
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(id)) return;
    location.replace('/g/?id=' + encodeURIComponent(id));
    return;
  }
  var i = location.pathname.match(/^\\/i\\/([^\\/?#]+)\\/?$/);
  if (i) {
    var token = decodeURIComponent(i[1]).trim();
    if (!/^[A-Za-z0-9_-]{16,128}$/.test(token)) return;
    location.replace('/i/?t=' + encodeURIComponent(token));
  }
})();"""

NOT_FOUND_CSP = (
    "default-src 'none'; img-src 'self'; style-src 'self'; font-src 'self'; "
    "script-src 'sha256-{hash}'; base-uri 'none'; form-action 'none'"
).format(hash=base64.b64encode(hashlib.sha256(NOT_FOUND_JS.encode("utf-8")).digest()).decode())

not_found = """<section class="handoff">
<div class="handoff-mark"><img src="/assets/icon.png" alt="" width="96" height="96"></div>
<p class="eyebrow">Page not found</p>
<h1>That page isn't here.</h1>
<p class="lede">The link may be old, or mistyped. Everything on the site is one
tap away below.</p>
<div class="hero-cta">
<a class="btn" href="/index.html">Home</a>
<a class="btn" href="/support.html">Support</a>
</div>
</section>
"""
(HERE / "404.html").write_text(
    page(
        "Not found",
        not_found,
        base="/",
        description="That page isn't here. GoBe — leave and find traces of daily moments.",
        csp=NOT_FOUND_CSP,
        head=f"<script>{NOT_FOUND_JS}</script>\n",
    ),
    encoding="utf-8",
)
print("wrote 404.html")
