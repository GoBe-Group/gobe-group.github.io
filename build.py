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
/* GoBe 1.5: the physical internet.
   Foil is the screen's layer, the technology wrapped round everyday life.
   Paper is the person's: what you walked, what you left. The page is paper,
   the foil is torn wherever the site says "go outside", and a biro line goes
   round the whole window the way the app draws one round its pages. */

@font-face{font-family:'Martian Mono';font-style:normal;font-weight:600;
  font-display:swap;src:url('fonts/martian-mono-semibold.woff2') format('woff2')}
@font-face{font-family:'Martian Mono';font-style:normal;font-weight:400;
  font-display:swap;src:url('fonts/martian-mono-regular.woff2') format('woff2')}
@font-face{font-family:'Caveat';font-style:normal;font-weight:700;
  font-display:swap;src:url('fonts/caveat-bold.woff2') format('woff2')}

:root{
  /* GoBeColors.swift, 1.5 */
  --paper:#F8FAFC; --paper-base:#EEF1F5; --paper-aged:#DFE4EC;
  --ink:#111114; --muted:#52535A; --faint:#7A8298;
  --biro:#0C1470; --ballpoint:#0A1BB0;
  --go:#90C808; --go-glow:#C4F03C; --go-dark:#4E7A00; --highlighter:#B4E02E;
  --be:#254BE0; --be-dark:#162C9A; --red:#E84C3D;
  --line:rgba(12,20,112,.16);
  --mono:'Martian Mono',ui-monospace,'SF Mono',Menlo,Consolas,monospace;
  --sans:'Avenir Next','Avenir','Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif;
  --digital:Arial,'Helvetica Neue',Helvetica,sans-serif;
  --hand:'Caveat','Bradley Hand','Segoe Print',cursive;
  --gutter:clamp(18px,4vw,40px);
  --max:1160px;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%; scroll-behavior:smooth}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:var(--sans); font-size:17px; line-height:1.6;
  -webkit-font-smoothing:antialiased; overflow-x:hidden;
}
/* paper fibre, as the app's paperGrain() */
body::before{
  content:""; position:fixed; inset:0; pointer-events:none; z-index:90;
  opacity:.035; mix-blend-mode:multiply; background-image:url('grain.svg');
}
/* the biro line round the window */
.frame{
  position:fixed; inset:7px; z-index:100; pointer-events:none;
  border:3.5px solid var(--biro); border-radius:30px;
  box-shadow:inset 1px -1px 0 rgba(12,20,112,.35);
}
img,video{max-width:100%; height:auto; display:block}
a{color:var(--be)}
a:hover{color:var(--be-dark)}
p{margin:0 0 16px}
ul{margin:0 0 16px; padding-left:22px}
li{margin:0 0 9px}
strong{font-weight:700}
/* Headings in the app's digital face: Arial pressed to 80% width, never bold.
   Set 125% wide and squashed back, so lines wrap where they will be seen. */
h1,h2,h3{font-family:var(--digital); font-weight:400; letter-spacing:-.01em; margin:0; color:var(--ink);
  text-wrap:balance; width:125%; transform:scaleX(.8); transform-origin:0 0}
.center h1,.center h2,.center h3,.closer h2,.handoff h1{transform-origin:50% 0; margin-left:-12.5% !important}
h1{font-size:clamp(34px,5.6vw,62px); line-height:1.04}
h2{font-size:clamp(32px,4.4vw,52px); line-height:1.05; margin:0 0 14px}
h3{font-size:clamp(18px,2vw,22px); line-height:1.2; margin:0 0 10px}
.bar{max-width:var(--max); margin:0 auto; padding:0 var(--gutter)}

/* Buttons: a drawn box and a pen shadow, pressed when you press them. */
.btn{
  display:inline-flex; align-items:center; gap:10px; justify-content:center;
  font-family:var(--mono); font-weight:600; font-size:13px; letter-spacing:-.01em;
  color:var(--biro); background:var(--paper); text-decoration:none;
  border:2px solid var(--biro); border-radius:14px; padding:13px 20px 12px;
  box-shadow:3px 3px 0 var(--biro); transition:transform .08s ease, box-shadow .08s ease;
}
.btn:hover{color:var(--biro); transform:translate(1px,1px); box-shadow:2px 2px 0 var(--biro)}
.btn:active{transform:translate(3px,3px); box-shadow:0 0 0 var(--biro)}
.btn.primary{background:var(--biro); color:#fff; box-shadow:3px 3px 0 var(--go)}
.btn.primary:hover{color:#fff; box-shadow:2px 2px 0 var(--go)}
.btn.primary:active{box-shadow:0 0 0 var(--go)}
.btn .apple{width:15px; height:18px; flex:none}

.eyebrow{font-family:var(--mono); font-size:12px; font-weight:600; letter-spacing:.02em;
  color:var(--biro); margin:0 0 14px; text-transform:lowercase}
.eyebrow::before{content:""; display:inline-block; width:22px; height:3px; border-radius:2px;
  background:var(--go); vertical-align:middle; margin:-2px 10px 0 0}
.lede{font-size:clamp(18px,1.6vw,20px); color:var(--muted); max-width:36em}
.note{font-size:13px; color:var(--faint)}
.note a{color:var(--muted)}
.whisper{font-family:var(--hand); font-weight:700; font-size:clamp(24px,2.4vw,30px);
  color:var(--ballpoint); line-height:1.1; transform:rotate(-2deg); display:inline-block}
.mono{font-family:var(--mono); font-size:14px}
.word{background:linear-gradient(transparent 58%,rgba(180,224,46,.6) 58%,rgba(180,224,46,.6) 90%,transparent 90%);
  padding:0 2px; font-weight:600; color:var(--ink)}

/* ---------- The header ---------- */
header.site{position:relative; z-index:20; padding:28px 0 18px}
header.site .bar{display:flex; align-items:center; justify-content:space-between; gap:20px; flex-wrap:wrap}
/* the wordmark on a scrap of paper, so its thin green Go holds on foil too */
.brand{display:inline-flex; text-decoration:none; background:var(--paper); border-radius:14px;
  padding:6px 14px 4px; transform:rotate(-2deg); box-shadow:0 8px 18px -10px rgba(12,20,60,.45),
  0 0 0 1px rgba(12,20,112,.08)}
.brand img{height:44px; width:auto}
nav.top{display:flex; align-items:center; gap:6px 22px; flex-wrap:wrap;
  font-family:var(--mono); font-size:12.5px; font-weight:600}
nav.top a{color:var(--ink); text-decoration:none; padding:4px 0; border-bottom:2.5px solid transparent}
nav.top a:hover{border-bottom-color:var(--go)}
nav.top a.active{border-bottom-color:var(--go)}
nav.top a.get{border:2px solid var(--biro); border-radius:12px; padding:8px 14px 7px;
  color:var(--biro); background:var(--paper); box-shadow:2px 2px 0 var(--biro)}
nav.top a.get:hover{transform:translate(1px,1px); box-shadow:1px 1px 0 var(--biro)}

/* ---------- Foil, and where it tears ---------- */
/* The wash is a layer of the background itself, so type holds on the
   brightest folds and both pseudo-elements are free for the torn edges. */
.foil{
  position:relative; color:var(--ink);
  background:linear-gradient(rgba(248,250,252,.42),rgba(248,250,252,.42)),
    #c9cbd2 url('foil.jpg') center/620px repeat;
}
.foil > .bar{position:relative; z-index:1}
.hero.foil{
  background:linear-gradient(100deg,rgba(248,250,252,.66) 0%,rgba(248,250,252,.36) 46%,rgba(248,250,252,0) 70%),
    #c9cbd2 url('foil.jpg') center/620px repeat;
}
.torn-below{padding-bottom:70px}
.torn-below::after{
  content:""; position:absolute; left:0; right:0; bottom:-1px; height:90px; pointer-events:none;
  background:url('torn.png') center bottom/1600px 90px repeat-x;
}
.torn-above{padding-top:90px}
.torn-above::before{
  content:""; position:absolute; left:0; right:0; top:-1px; height:90px; pointer-events:none;
  background:url('torn-top.png') center top/1600px 90px repeat-x;
}

/* ---------- Home: the 1.6 loop, one chapter per App Store slide ---------- */
main.home header.site{position:absolute; left:0; right:0; top:0}
section{position:relative}
.band{padding:clamp(56px,7.5vw,104px) 0}
.band.tight{padding-top:clamp(40px,6vw,72px)}
.center{text-align:center}

/* The ground the slides are printed on: foil paper with the crumple over it.
   The slide crops sit on the same foil, faded at their edges into it. */
main.home{
  background:url('crumple.jpg') center top/1200px repeat, url('foil-paper.jpg') center top/940px repeat;
  background-blend-mode:overlay, normal;
}

.swipe{position:relative; z-index:0; white-space:nowrap}
.swipe::before{content:""; position:absolute; z-index:-1; left:-5%; right:-5%; top:30%; bottom:-4%;
  background:url('deco/swipe.png') center/100% 100% no-repeat; opacity:.95}

.hero{padding:clamp(120px,13vw,150px) 0 clamp(20px,4vw,40px)}
.hero .bar,.chapter .bar{display:grid; grid-template-columns:1fr 1fr; gap:clamp(20px,5vw,72px); align-items:center}
.hero h1{font-size:clamp(46px,7.4vw,92px); margin:0 0 4px}
.hero .whisper,.chapter .whisper{font-size:clamp(26px,2.8vw,36px); margin:0 0 22px 2px; transform:rotate(-2deg)}
.hero .btns{display:flex; flex-wrap:wrap; gap:14px 18px; align-items:center; margin:26px 0 14px}
.store img{width:180px; height:auto}
.hero .note{color:var(--muted)}

.ch-body p{color:#33343c; max-width:30em}
.ch-body strong{color:var(--ink)}

/* the picture: the slide's own phone and lifted bits, faded into the foil */
.ch-pic{justify-self:center; width:min(100%,430px)}
.hero-pic{width:min(100%,470px)}
.ch-pic img{width:100%;
  -webkit-mask-image:radial-gradient(ellipse 72% 70% at 50% 50%,#000 72%,transparent 100%);
          mask-image:radial-gradient(ellipse 72% 70% at 50% 50%,#000 72%,transparent 100%)}

/* the rest of the loop, as an index */
.loop{padding:8px 0 clamp(10px,3vw,30px)}
.loop .bar{display:flex; align-items:center; gap:10px 22px; flex-wrap:wrap}
.loop .whisper{margin:0; font-size:28px}
.loop ol{list-style:none; display:flex; flex-wrap:wrap; gap:10px; margin:0; padding:0}
.loop li{margin:0}
.loop a{display:inline-flex; align-items:baseline; gap:8px; text-decoration:none; color:var(--ink);
  background:rgba(255,255,255,.72); border:2px solid var(--biro); border-radius:12px;
  padding:7px 12px 6px; box-shadow:2px 2px 0 var(--biro); font-size:14.5px}
.loop a b{font-family:var(--hand); font-size:19px; color:var(--ballpoint); line-height:1}
.loop a:hover{transform:translate(1px,1px); box-shadow:1px 1px 0 var(--biro)}

.chapter{padding:clamp(20px,3.5vw,44px) 0}
.chapter.rev .ch-copy{order:2}
.chapter h2{font-size:clamp(40px,5.6vw,70px); line-height:1.02; margin:0 0 4px}
.ch-num{font-family:var(--hand); font-weight:700; font-size:34px; color:var(--ballpoint); margin:0 0 8px; line-height:1}
.ch-num span{font-size:20px; color:var(--faint); margin-left:4px}
/* the walk line, from each chapter to the next, the lime line through the slides */
.chapter::before{content:""; position:absolute; left:50%; top:-40px; width:3px; height:80px;
  background:repeating-linear-gradient(var(--go) 0 10px,transparent 10px 18px); border-radius:2px}

.privacy .two{display:grid; grid-template-columns:.9fr 1.1fr; gap:clamp(24px,5vw,64px); align-items:start}
.privacy .lede{margin-top:10px}
.sheet{background:#fff; border:2px solid var(--biro); border-radius:24px; padding:30px 30px 14px;
  box-shadow:4px 4px 0 var(--biro)}
.sheet p{color:var(--muted)}
.values{display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-top:44px}
.value{border-top:3px solid var(--biro); padding-top:14px}
.value .vtitle{font-family:var(--digital); font-size:19px; margin-bottom:6px}
.value p{font-size:14px; color:var(--muted); margin:0}

.facts{display:grid; grid-template-columns:1fr 1fr; gap:0 28px; margin:26px 0 18px;
  border-top:2px solid var(--biro)}
.fact{display:flex; justify-content:space-between; gap:18px; padding:12px 0; border-bottom:1px solid var(--line)}
.fact .k{font-family:var(--mono); font-size:12px; font-weight:600; color:var(--biro); text-transform:lowercase; white-space:nowrap}
.fact .v{font-size:15px; text-align:right}

.closer{padding:clamp(56px,8vw,96px) 0 clamp(80px,10vw,120px); text-align:center}
.closer .icon{width:116px; margin:0 auto 22px; border-radius:26px; filter:drop-shadow(0 18px 28px rgba(12,20,60,.35))}
.closer h2{font-size:clamp(40px,6vw,72px); margin:0 0 4px}
.closer .whisper{margin:0 0 18px}
.closer .lede{margin:0 auto; color:#2a2b33}
.closer .btns{display:flex; flex-wrap:wrap; justify-content:center; align-items:center; gap:14px; margin-top:26px}

/* ---------- Reading pages (legal, support) ---------- */
main.col{max-width:780px; margin:0 auto; padding:26px var(--gutter) 70px}
main.col h1{font-size:clamp(32px,5vw,50px); margin:0 0 12px}
main.col h2{font-size:clamp(20px,2.4vw,25px); margin:42px 0 12px}
main.col h3{font-size:18px; margin:26px 0 8px}
main.col .lede{margin-bottom:28px}
.stamp{display:inline-block; font-family:var(--mono); font-size:12px; font-weight:600;
  color:var(--biro); border:2px solid var(--biro); border-radius:10px; padding:6px 12px 5px;
  transform:rotate(-1.5deg); margin:6px 0 28px; background:#fff}
.card{background:#fff; border:2px solid var(--biro); border-radius:22px; padding:24px 26px 10px;
  box-shadow:4px 4px 0 var(--biro); margin:0 0 26px}
.card h2{margin-top:0}
.flush{margin-bottom:12px}
main.col table{border-collapse:collapse; width:100%; margin:0 0 20px; font-size:15px}
main.col th,main.col td{border-bottom:1px solid var(--line); padding:9px 8px; text-align:left; vertical-align:top}
main.col th{font-family:var(--mono); font-size:12px; color:var(--biro)}
main.col blockquote{margin:0 0 16px; padding:4px 0 4px 18px; border-left:3px solid var(--go); color:var(--muted)}

/* ---------- Handoff pages (/u/, /g/, /i/, /f/, 404) ---------- */
.handoff{text-align:center; padding:12px 0 18px}
.handoff-mark img{width:108px; height:108px; margin:0 auto 22px; border-radius:24px;
  box-shadow:0 14px 28px -12px rgba(12,20,60,.45)}
.handoff h1{font-size:clamp(28px,4.6vw,42px); margin:0 0 12px}
.handoff .lede{margin:0 auto 22px}
.hero-cta{display:flex; flex-wrap:wrap; gap:14px; justify-content:center; margin:24px 0 18px}
.invite-code{display:inline-block; font-family:var(--mono); font-weight:600; font-size:clamp(30px,6vw,44px);
  letter-spacing:.12em; color:var(--ink); padding:6px 22px 4px; margin:4px 0 14px; border-radius:14px;
  background:linear-gradient(transparent 12%,rgba(180,224,46,.75) 12%,rgba(180,224,46,.75) 92%,transparent 92%)}

/* ---------- Footer ---------- */
footer.site{border-top:2px solid var(--biro); margin-top:0; padding:26px 0 44px; font-size:13px; color:var(--muted)}
footer.site .bar{display:flex; justify-content:space-between; gap:18px 40px; flex-wrap:wrap; align-items:flex-start}
footer.site p{margin:0; max-width:560px}
footer.site nav{display:flex; gap:18px; font-family:var(--mono); font-size:12px; font-weight:600}
footer.site nav a{color:var(--biro); text-decoration:none}
footer.site nav a:hover{text-decoration:underline}

/* ---------- Narrow screens ---------- */
@media (max-width:900px){
  .hero .bar,.chapter .bar,.privacy .two{grid-template-columns:1fr}
  .chapter.rev .ch-copy{order:0}
  .ch-pic{width:min(100%,440px)}
  .values{grid-template-columns:1fr 1fr}
  .facts{grid-template-columns:1fr}
}
@media (max-width:560px){
  body{font-size:16px}
  .frame{inset:4px; border-width:3px; border-radius:22px}
  header.site{padding-top:22px}
  .brand img{height:38px}
  /* one row on a phone: the wordmark and the way to the App Store; the
     rest is in the footer and the hero */
  header.site .bar{flex-wrap:nowrap}
  nav.top a:not(.get){display:none}
  nav.top a.get{padding:7px 12px 6px; font-size:12px}
  .values{grid-template-columns:1fr}
  .fact{flex-direction:column; gap:2px}
  .fact .v{text-align:left}
  .btn{padding:12px 16px 11px}
  .loop{display:none}
  .chapter::before{display:none}
}

/* ---------- The odd drawn mark ---------- */
.brief h2{display:inline-block; position:relative}
.brief h2::after{content:""; position:absolute; left:-2%; right:-6%; bottom:-16px; height:18px;
  background:url('deco/underline.png') center/100% 100% no-repeat}
main.col h1::after{content:""; display:inline-block; width:.62em; height:.62em; margin-left:.28em;
  background:url('deco/star.png') center/contain no-repeat; transform:rotate(12deg) translateY(-.12em)}
.handoff-mark{position:relative; display:inline-block}
.handoff-mark::after{content:""; position:absolute; width:96px; height:34px; top:-12px; right:-38px;
  background:url('deco/tape.png') center/contain no-repeat; transform:rotate(30deg)}

/* ---------- A Windows 98 window, gone over in biro ---------- */
.win{position:relative; max-width:900px; margin:0 auto; background:#fff; border:2px solid var(--biro); border-radius:10px;
  box-shadow:5px 5px 0 var(--biro); overflow:hidden}
.win-bar{display:flex; align-items:center; gap:7px; background:var(--biro); color:#fff;
  font-family:var(--mono); font-size:12px; font-weight:600; padding:8px 12px}
.win-bar span{flex:1}
.win-bar i{display:inline-block; width:17px; height:15px; border:1.5px solid #fff; border-radius:3px}
.win-body{padding:28px 32px 20px}
.brief .win-body > p{color:var(--muted); max-width:44em}

@media (max-width:560px){ .win-body{padding:22px 18px 14px} }

@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  .btn,nav.top a.get{transition:none}
}

/* /film: the 1.5 launch film on its own page, for sharing. Square on a
   desktop, the vertical cut on a phone. */
.launch-film{display:block;width:100%;max-width:640px;aspect-ratio:1/1;margin:28px auto 8px;
  border-radius:22px;background:#dfe3ea;box-shadow:0 24px 50px rgba(16,26,69,.18)}
.launch-film.tall{display:none}
.store-badge{display:inline-block;margin:18px auto 4px}
.store-badge img{display:block;width:220px;height:auto}
@media (max-width:700px){.launch-film.square{display:none}
  .launch-film.tall{display:block;max-width:420px;aspect-ratio:9/16;max-height:82vh}}
"""

GRAIN_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="140" height="140">'
             '<filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" '
             'numOctaves="2" stitchTiles="stitch"/></filter>'
             '<rect width="100%" height="100%" filter="url(#n)"/></svg>')


def deco(name, cls, keep=False):
    """One piece of the collage kit, tucked in somewhere: decoration only, so
    hidden from assistive tech, and most of it dropped on a phone (`keep`
    marks the few that stay)."""
    with open(HERE / "assets" / "deco" / f"{name}.png", "rb") as f:
        head = f.read(24)
    w, h = int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")
    extra = " keep" if keep else ""
    return (f'<img class="deco {cls}{extra}" src="assets/deco/{name}.png" alt="" aria-hidden="true" '
            f'width="{w}" height="{h}" loading="lazy">')


def page(title, body, active="", wrap_class="", base="", description="", csp=CSP, head=""):
    """Render a full page. `base` prefixes every internal link — pass "/" for
    pages that don't live at the site root (e.g. /u/), so assets still resolve.

    `csp` and `head` exist for the one page that needs a script (/u/, which has
    to reach an installed app); every other page keeps the script-free default."""
    def nav(href, label):
        cls = ' class="active"' if active == href else ""
        return f'<a href="{base}{href}"{cls}>{label}</a>'
    main_class = wrap_class or "col"
    desc = description or f"GoBe: leave and find traces of daily moments. {title}."
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
<link rel="apple-touch-icon" href="{base}assets/apple-touch-icon.png">
<link rel="stylesheet" href="{base}assets/style.css">
{head}</head>
<body>
<div class="frame" aria-hidden="true"></div>
<main class="{main_class}">
<header class="site"><div class="bar">
<a class="brand" href="{base}index.html"><img src="{base}assets/gobe-logo.png" alt="GoBe" width="520" height="231"></a>
<nav class="top">{nav('index.html#how','How it works')}{nav('privacy.html','Privacy')}{nav('terms.html','Terms')}{nav('support.html','Support')}<a class="get" href="{APP_STORE_URL}">Get the app</a></nav>
</div></header>
{body}
</main>
<footer class="site"><div class="bar">
<p>GoBe is operated by Hamed Bakayoko, sole trader trading as GoBe, 124 City Road, London EC1V 2NX, United Kingdom.
Contact: <a href="mailto:{CONTACT}">{CONTACT}</a> · Governing law: England &amp; Wales.</p>
<nav><a href="{base}privacy.html">Privacy</a><a href="{base}terms.html">Terms</a><a href="{base}support.html">Support</a></nav>
</div></footer>
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
                            {"/": "/f/", "comment": "friend invite links"},
                            {"/": "/f/*", "comment": "friend invite links (path form)"},
                            {"/": "/gift/", "comment": "gift links"},
                            {"/": "/gift/*", "comment": "gift links (path form)"},
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
#
# Every page also carries the security headers a <meta> tag can't set (27 Sep
# 2026 audit): HTTPS remembered for a year, no framing by other sites, no
# content-type guessing, and none of the phone's sensors asked for. The strict
# per-page CSP stays in each page's <meta>; the header one only adds
# frame-ancestors, which a <meta> CSP ignores.
(HERE / "_headers").write_text(
    "/*\n"
    "  Strict-Transport-Security: max-age=31536000; includeSubDomains\n"
    "  X-Content-Type-Options: nosniff\n"
    "  X-Frame-Options: DENY\n"
    "  Content-Security-Policy: frame-ancestors 'none'\n"
    "  Referrer-Policy: strict-origin-when-cross-origin\n"
    "  Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()\n"
    "  Cross-Origin-Opener-Policy: same-origin\n"
    "\n"
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
# The page tells the 1.6 loop in the order the App Store screenshots do, one
# chapter per slide: your area is full of secrets, tear open what people left,
# treats near you, keep what you find, gift it, cross paths and swap, make your
# page yours. Each chapter's picture is that slide's own phone (headline cropped
# off, the page sets it in type instead), so the store and the site tell one
# story. Then how it stays safe, the short version for press, and the way in.
HOME_TITLE = "Your area is full of secrets"
HOME_DESC = (
    "GoBe is the social network on a map. Walk to unwrap what people left round here, "
    "find free treats near you, keep what you find and gift it to friends. Free on iPhone."
)

# The seven chapters: (id, headline with _swiped_ word, whisper, body, alt).
CHAPTERS = [
    ("secrets", "Your area is full of _secrets_", "walk to unwrap them",
     """<p>Notes, photos and finds are pinned to the streets round you, each one
sealed in foil on the map. You can see they're there. You can't see what they
say from the sofa.</p>
<p>Press play and walk. The fog lifts behind you, and whatever you walk up to
opens.</p>""",
     "The GoBe map of Soho, its streets dotted with sealed traces wrapped in blue, gold and pink foil"),
    ("tear", "Tear open what people _left_", "sealed till you walk up to it",
     """<p>Get close and the foil comes off. Inside is a <strong>trace</strong>: a line,
a photo or a film someone left on that exact spot. A second-hand shop with
everything under a tenner. The bench that gets the last of the sun.</p>
<p>Like it, reply, or retrace it onto your own map. Then leave one of your own
for whoever comes along next.</p>""",
     "A sealed trace torn open in GoBe, reading: Second hand shop, everything under a tenner today"),
    ("treats", "Uncover _treats_ near you", "free museums, gigs, deals &amp; more",
     """<p>Some of what's sealed out there is for you to use: a free pastry with
your coffee, a museum that costs nothing on a Sunday, a gig round the corner,
a deal in a shop you walk past every day.</p>
<p>Walk up, unwrap it, and collect it at the door.</p>""",
     "An in-store offer unwrapped in GoBe: free pastry with any coffee, with a Collect it button"),
    ("keep", "Keep everything you _find_", "every sticker, note &amp; photo",
     """<p>Everything you open goes into your <strong>storage</strong>. Traces you
kept, and a sticker from every kind of place you've been: the bakery, the
park, the planetarium, the gig.</p>
<p>It fills up the more you go out. Nobody can buy a sticker. You have to
have been there.</p>""",
     "GoBe storage, a shelf of stickers found at real places, with a treasure chest beside it"),
    ("gift", "Gift your finds to _friends_", "up to ten things in one bag",
     """<p>Pick things from your storage, a trace, a sticker, an offer, and put
them in a <strong>gift bag</strong>. Seal it and send it to a friend.</p>
<p>Not on GoBe yet? Send the gift by text. It waits for them, still sealed,
for thirty days.</p>""",
     "Packing a gift bag for a friend in GoBe, ten finds in the bag and a sealed foil parcel beside it"),
    ("cross", "Cross paths, _swap_ gifts", "pass someone out walking: you each get one",
     """<p>Out on a walk at the same time as someone, a street apart? You've
<strong>crossed</strong>. You each find the other in your drawer, face and name
and nothing else, and a gift to open.</p>
<p>It's off until you turn it on, it only happens while you're walking, and
GoBe never says where or when.</p>""",
     "A gift from someone you crossed paths with in GoBe, a foil parcel waiting to be opened"),
    ("page", "Make your page _yours_", "deck it out with things you find",
     """<p>Your page is a scrapbook of where you've been. Pick a look, pin a trace
you love, add GIFs, and stick on the stickers you found.</p>
<p>Every page is different, because nobody walked your walks.</p>""",
     "Three GoBe profile pages fanned out, the front one decorated with a pinned trace, GIFs and found stickers"),
]


def swiped(text):
    """`_word_` gets the lime highlighter swipe behind it, as in the app."""
    return re.sub(r"_([^_]+)_", r'<span class="swipe">\1</span>', text)


def chapter(i, ch):
    cid, head, whisper, body, alt = ch
    n = i + 1
    side = "rev" if i % 2 else ""
    return f"""<section class="chapter {side}" id="{cid}">
<div class="bar">
<div class="ch-copy">
<p class="ch-num">0{n}<span>/07</span></p>
<h2>{swiped(head)}</h2>
<p class="whisper">{whisper}</p>
<div class="ch-body">
{body}
</div>
</div>
<div class="ch-pic"><img src="assets/story/s{n}.jpg" width="880" height="1405" loading="lazy" alt="{alt}"></div>
</div>
</section>"""


LOOP_NAV = "\n".join(
    f'<li><a href="#{c[0]}"><b>0{i + 1}</b>{re.sub(r"_", "", c[1])}</a></li>'
    for i, c in enumerate(CHAPTERS[1:], start=1)
)

BADGE = (f'<a class="store" href="{APP_STORE_URL}"><img src="assets/appstore-badge.svg" '
         f'alt="Download on the App Store" width="180" height="60"></a>')

home = f"""<section class="hero" id="secrets">
<div class="bar">
<div class="hero-copy">
<p class="eyebrow">The social network on a map</p>
<h1>{swiped(CHAPTERS[0][1])}</h1>
<p class="whisper">{CHAPTERS[0][2]}</p>
<div class="ch-body">
{CHAPTERS[0][3]}
</div>
<div class="btns">{BADGE}<a class="btn" href="#tear">See how it works</a></div>
<p class="note">Free on iPhone · Made in the UK · Ages 16+</p>
</div>
<div class="ch-pic hero-pic"><img src="assets/story/s1.jpg" width="880" height="1405" fetchpriority="high"
  alt="{CHAPTERS[0][4]}"></div>
</div>
</section>

<nav class="loop" aria-label="The GoBe loop">
<div class="bar">
<p class="whisper">then what?</p>
<ol>
{LOOP_NAV}
</ol>
</div>
</nav>

{chr(10).join(chapter(i, c) for i, c in enumerate(CHAPTERS) if i)}

<section class="band privacy" id="privacy">
<div class="bar two">
<div>
<p class="eyebrow">Privacy</p>
<h2>Your exact location stays <span class="swipe">off</span> the map.</h2>
<p class="lede">A map of real places has to keep people safe at them. Here's how GoBe does it.</p>
</div>
<div class="sheet">
<p>Traces are saved to a rough spot on a grid about thirty metres across. The exact point is
never stored, on your phone or on our servers.</p>
<p>Your walks stay private to you. Crossing paths is off until you turn it on, and works
from a block about a hundred metres across, never a point.</p>
<p>Mark home, work or anywhere else as protected and GoBe keeps traces out of it and goes
quiet inside it. Protected areas stay on your phone.</p>
<p>GoBe is free, carries no ads and never sells your data. The detail is in the
<a href="privacy.html">Privacy Policy</a>.</p>
</div>
</div>
<div class="bar">
<div class="values">
<div class="value"><div class="vtitle">Free</div><p>Nothing to pay and no ads.</p></div>
<div class="value"><div class="vtitle">Your data is yours</div><p>We never sell it. Delete your account and everything in it whenever you like.</p></div>
<div class="value"><div class="vtitle">Made in the UK</div><p>An independent app, made in Britain.</p></div>
<div class="value"><div class="vtitle">16 and over</div><p>Younger users start on stricter privacy settings.</p></div>
</div>
</div>
</section>

<section class="band tight brief" id="about">
<div class="bar">
<div class="win">
<div class="win-bar"><span>about-gobe.txt</span><i></i><i></i><i></i></div>
<div class="win-body">
<p class="eyebrow">For investors, partners and press</p>
<h2>The short version.</h2>
<p>Social networks got very good at keeping people on their phones. GoBe is built to get them
out of the house. You post by standing somewhere, what you can open depends on where you are,
and the app is working when somebody goes out.</p>
<p>The map is the moat. It's filled in street by street by the people who walk them, it can't
be copied into another city, and every trace, treat and find makes it more worth walking for
everyone nearby. GoBe grows the way a place does, one street at a time.</p>
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
</div>
</div>
</section>

<section class="closer">
<div class="bar">
<img class="icon" src="assets/icon-rounded.png" alt="" width="240" height="240">
<h2>Go and find <span class="swipe">something</span>.</h2>
<p class="whisper">it's round the corner. probably.</p>
<p class="lede">GoBe is free on the App Store for iPhone.</p>
<div class="btns">{BADGE}<a class="btn" href="support.html">Support</a></div>
</div>
</section>
"""
# Invites shared before the /f/ page existed read gobeapp.co.uk/?invite=CODE.
# They land here; this sends them on to the page that does the job.
HOME_JS = """(function(){
  var c = new URLSearchParams(location.search).get('invite');
  if (c && /^[A-Za-z0-9]{4,12}$/.test(c)) {
    location.replace('/f/?c=' + encodeURIComponent(c.toUpperCase()));
  }
})();"""
HOME_CSP = (
    "default-src 'none'; img-src 'self'; media-src 'self'; style-src 'self'; font-src 'self'; "
    "script-src 'sha256-{hash}'; base-uri 'none'; form-action 'none'"
).format(hash=base64.b64encode(hashlib.sha256(HOME_JS.encode("utf-8")).digest()).decode())

(HERE / "index.html").write_text(
    page(HOME_TITLE, home, "index.html", "home", description=HOME_DESC,
         csp=HOME_CSP, head=f"<script>{HOME_JS}</script>\n"),
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
<div class="handoff-mark"><img src="/assets/icon-rounded.png" alt="" width="108" height="108"></div>
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
        description="Open this GoBe profile in the app. GoBe: leave and find traces of daily moments.",
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
<div class="handoff-mark"><img src="/assets/icon-rounded.png" alt="" width="108" height="108"></div>
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
        description="Open this GoBe community or event in the app. GoBe: leave and find traces of daily moments.",
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
<div class="handoff-mark"><img src="/assets/icon-rounded.png" alt="" width="108" height="108"></div>
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
        description="Open your GoBe invite in the app. GoBe: leave and find traces of daily moments.",
        csp=INVITE_CSP,
        head=f"<script>{INVITE_JS}</script>\n",
    ),
    encoding="utf-8",
)
print("wrote i/index.html")

# --- /gift/ : a gift made for somebody not on GoBe yet ----------------------
#
# Where a gift link lands (/gift/?t=CODE, sent by text from the app's gift
# composer) when iOS didn't hand it to the app: the association file claims
# /gift/, so with GoBe installed the link opens it directly. Until 18 Oct 2026
# there was no page here at all, and every gift sent by text opened on the 404.
#
# Like /i/, the code is a way in rather than a name: whoever opens it in the
# app is handed the gift, so the page renders nothing about it (not who sent
# it, not the code) and sends no referrer. The code is checked against the
# app's own alphabet before it goes anywhere near the scheme link.
GIFT_JS = f"""(function(){{
  var STORE = {json.dumps(APP_STORE_URL)};
  var q = new URLSearchParams(location.search);
  // Accept both shapes: /gift/?t=<code> (what we send) and /gift/<code>.
  var raw = q.get('t');
  if (!raw) {{
    try {{ raw = decodeURIComponent(location.pathname.replace(/^\\/gift\\/?/, '')); }}
    catch (e) {{ raw = ''; }}
  }}
  var code = (raw || '').toUpperCase().replace(/[\\s-]/g, '').replace(/\\/+$/, '');
  var ok = /^[A-HJ-NP-Z2-9]{{8}}$/.test(code);
  var appURL = ok ? '{APP_SCHEME}://gift/?t=' + encodeURIComponent(code) : null;
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

GIFT_CSP = (
    "default-src 'none'; img-src 'self'; style-src 'self'; font-src 'self'; "
    "script-src 'sha256-{hash}'; base-uri 'none'; form-action 'none'"
).format(hash=base64.b64encode(hashlib.sha256(GIFT_JS.encode("utf-8")).digest()).decode())

gift = f"""<section class="handoff">
<div class="handoff-mark"><img src="/assets/icon-rounded.png" alt="" width="108" height="108"></div>
<p class="eyebrow">Somebody wrapped you a gift</p>
<h1>Unwrap it in GoBe.</h1>
<p class="lede">A gift link opens straight in the app, still sealed. If GoBe
isn't on this iPhone yet, you'll be taken to the App Store to get it: once it's
on, tap the link again and the gift is there. It waits for you for 30 days.</p>
<div class="hero-cta">
<a class="btn" id="open-in-app" href="{APP_STORE_URL}">Open in GoBe</a>
<a class="btn" href="{APP_STORE_URL}">Get GoBe</a>
</div>
<p class="note">Free on the App Store · Made in the UK · For ages 16+</p>
<p class="note"><a href="/index.html">What is GoBe?</a> · <a href="/support.html">Need a hand?</a></p>
</section>

<div class="card">
<h2>What is this?</h2>
<p>Somebody on GoBe made you a <strong>gift bag</strong>: things they wrote or
photographed, stickers they found, a deal. Join GoBe to open it and the two of
you are friends. Already on GoBe? You get the gift, and an add from them that
is yours to say yes or no to.</p>
<h2>Why can't I see it here?</h2>
<p>This page shows nothing about the gift on purpose. A link can be forwarded
and a web page is public, so naming who sent it here would hand that to anyone
the link reached.</p>
<p class="flush">More on how we handle your data in our
<a href="/privacy.html">Privacy Policy</a>.</p>
</div>
"""
(HERE / "gift").mkdir(exist_ok=True)
(HERE / "gift" / "index.html").write_text(
    page(
        "Gift",
        gift,
        base="/",
        description="Unwrap your GoBe gift in the app. GoBe: leave and find traces of daily moments.",
        csp=GIFT_CSP,
        head=f"<script>{GIFT_JS}</script>\n",
    ),
    encoding="utf-8",
)
print("wrote gift/index.html")

# --- /f/ : a friend's invite code ------------------------------------------
#
# Where a friend's invite link lands (/f/?c=CODE). The link is for getting
# GoBe, so the page goes on to the App Store by itself after a moment, long
# enough to see the code. The button copies the code on the way out for
# anybody quicker than that (a tap is the only moment a page may write to the
# clipboard). Once GoBe is on the phone the same link opens the app instead
# (the association file claims /f/), and the app fills the code in itself.
# `?noauto=1` holds the page still, for looking at it.
#
# A code is not a secret the way a gathering invite is: it is meant to be
# typed and shown, so showing it here costs nothing.
FRIEND_JS = f"""(function(){{
  var STORE = {json.dumps(APP_STORE_URL)};
  var q = new URLSearchParams(location.search);
  var raw = q.get('c');
  if (!raw) {{
    try {{ raw = decodeURIComponent(location.pathname.replace(/^\\/f\\/?/, '')); }}
    catch (e) {{ raw = ''; }}
  }}
  var code = (raw || '').trim().replace(/\\/+$/, '').toUpperCase();
  var ok = /^[A-Z0-9]{{4,12}}$/.test(code);
  var auto = q.get('noauto') !== '1';
  var gone = false;
  function go() {{ if (!gone) {{ gone = true; location.replace(STORE); }} }}

  function start() {{
    var shown = document.getElementById('invite-code');
    var get = document.getElementById('get-gobe');
    var open = document.getElementById('open-in-app');
    if (shown) shown.textContent = ok ? code : '';
    if (!ok) {{
      var box = document.getElementById('code-box');
      if (box) box.hidden = true;
    }}
    if (open && ok) open.href = '{APP_SCHEME}://f/?c=' + encodeURIComponent(code);
    if (get) {{
      get.addEventListener('click', function (event) {{
        if (!ok || !navigator.clipboard) return;
        event.preventDefault();
        navigator.clipboard.writeText(code).then(go, go);
      }});
    }}
    if (auto) setTimeout(go, 1600);
  }}

  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', start);
  }} else {{
    start();
  }}
}})();"""

FRIEND_CSP = (
    "default-src 'none'; img-src 'self'; style-src 'self'; font-src 'self'; "
    "script-src 'sha256-{hash}'; base-uri 'none'; form-action 'none'"
).format(hash=base64.b64encode(hashlib.sha256(FRIEND_JS.encode("utf-8")).digest()).decode())

friend = f"""<section class="handoff">
<div class="handoff-mark"><img src="/assets/icon-rounded.png" alt="" width="108" height="108"></div>
<p class="eyebrow">A friend invited you</p>
<h1>Get GoBe, and bring their code.</h1>
<div id="code-box">
<p class="lede">Your invite code</p>
<p class="invite-code" id="invite-code"></p>
<p class="note">Taking you to the App Store. Once GoBe is on your phone, open
this link again and the code goes in by itself: it puts points on your GoBe
Score straight away, and on theirs once you leave your first trace.</p>
</div>
<div class="hero-cta">
<a class="btn" id="get-gobe" href="{APP_STORE_URL}">Get GoBe</a>
<a class="btn" id="open-in-app" href="{APP_STORE_URL}">Already have it? Open GoBe</a>
</div>
<p class="note">Free on the App Store · Made in the UK · For ages 16+</p>
<p class="note"><a href="/index.html">What is GoBe?</a> · <a href="/support.html">Need a hand?</a></p>
</section>
"""
(HERE / "f").mkdir(exist_ok=True)
(HERE / "f" / "index.html").write_text(
    page(
        "You're invited",
        friend,
        base="/",
        description="A friend invited you to GoBe. Get the app and bring their invite code.",
        csp=FRIEND_CSP,
        head=f"<script>{FRIEND_JS}</script>\n",
    ),
    encoding="utf-8",
)
print("wrote f/index.html")

# ─── /film: the launch film, on a page of its own to link to ────────────────
# The film files break the Cloudflare Workers build whenever they are in this
# repo (even ignored), so they live in GoBe-Group/gobe-films on GitHub Pages.
FILM_HOST = "https://gobe-group.github.io"
# GoBe is on every storefront now, and the country-less link sends each
# visitor to their own (checked 29 Sep 2026; it used to 404 when UK-only).
APP_STORE_GLOBAL_URL = f"https://apps.apple.com/app/{APP_STORE_SLUG}/id{APP_STORE_ID}"
FILM_DIR = FILM_HOST + "/gobe-films/launch"
FILM_CSP = (
    "default-src 'none'; img-src 'self'; media-src 'self' " + FILM_HOST + "; style-src 'self'; font-src 'self'; "
    "base-uri 'none'; form-action 'none'"
)
film = f"""<section class="handoff">
<p class="eyebrow">GoBe 1.5</p>
<h1>The internet is outside.</h1>
<p class="lede">GoBe is a map of photos and notes that people leave where they are.
You can only open one where it was left, so you walk there.</p>
<video class="launch-film square" src="{FILM_DIR}/launch-square.mp4" controls playsinline preload="metadata"
  poster="/assets/films/launch.jpg" aria-label="The GoBe launch film"></video>
<video class="launch-film tall" src="{FILM_DIR}/launch-vertical.mp4" controls playsinline preload="none"
  poster="/assets/films/launch-vertical.jpg" aria-label="The GoBe launch film"></video>
<a class="store-badge" href="{APP_STORE_GLOBAL_URL}"><img src="/assets/appstore-badge.svg" alt="Download on the App Store" width="240" height="80"></a>
<p class="note">Free on iPhone · For ages 16+</p>
<p class="note"><a href="/index.html">How it works</a> · <a href="/privacy.html">Privacy</a> · <a href="mailto:{CONTACT}">{CONTACT}</a></p>
</section>
"""
(HERE / "film").mkdir(exist_ok=True)
(HERE / "film" / "index.html").write_text(
    page(
        "The internet is outside",
        film,
        base="/",
        description="GoBe is a map of photos and notes people leave where they are. You can only open one where it was left.",
        csp=FILM_CSP,
    ),
    encoding="utf-8",
)
print("wrote film/index.html")


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
<div class="handoff-mark"><img src="/assets/icon-rounded.png" alt="" width="108" height="108"></div>
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
        description="That page isn't here. GoBe: leave and find traces of daily moments.",
        csp=NOT_FOUND_CSP,
        head=f"<script>{NOT_FOUND_JS}</script>\n",
    ),
    encoding="utf-8",
)
print("wrote 404.html")
