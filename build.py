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
h1,h2,h3{font-family:var(--mono); font-weight:600; letter-spacing:-.035em; margin:0; color:var(--ink); text-wrap:balance}
h1{font-size:clamp(34px,5.6vw,62px); line-height:1.04}
h2{font-size:clamp(25px,3.4vw,38px); line-height:1.1; margin:0 0 14px}
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
  color:var(--biro); line-height:1.1; transform:rotate(-2deg); display:inline-block}
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

/* ---------- Home ---------- */
main.home header.site{position:absolute; left:0; right:0; top:0}
.hero{padding-top:118px}
.hero .bar{position:relative; display:grid; grid-template-columns:1.12fr .88fr; gap:clamp(24px,5vw,72px); align-items:center}
.hero h1{margin:0 0 20px}
.hero .lede{color:#2a2b33}
.hero .btns{display:flex; flex-wrap:wrap; gap:14px 18px; align-items:center; margin:28px 0 18px}
.hero .note{color:#3c3e48}
.hero-media{position:relative; justify-self:center; width:min(100%,360px); margin-bottom:-120px; z-index:3}
.hero-media .whisper{position:absolute; left:-215px; bottom:150px; z-index:4; color:var(--biro); white-space:nowrap}

/* A phone: black glass round a capture, the capture cut to its corners. */
.phone{position:relative; background:#0b0b0e; border-radius:13.5% / 6.3%; padding:3.2%;
  box-shadow:0 0 0 1.5px #6b6d75, 0 0 0 3px #26272c, 0 26px 50px -18px rgba(12,20,60,.45)}
.phone img{border-radius:10.8% / 5%; width:100%; height:auto}
.phone::after{ /* the island */
  content:""; position:absolute; left:50%; top:3.9%; width:27%; height:3.1%;
  transform:translateX(-50%); background:#000; border-radius:99px}

section{position:relative}
.band{padding:clamp(56px,7.5vw,104px) 0}
.band.tight{padding-top:clamp(40px,6vw,72px)}
.center{text-align:center}
.center .lede{margin-left:auto; margin-right:auto}

/* The idea, over the photograph of a route torn through foil. */
.idea .bar{display:grid; grid-template-columns:1fr 1fr; gap:clamp(28px,5vw,70px); align-items:center}
.idea .pic{position:relative}
.idea .pic img:not(.deco):not(.tape){border-radius:22px; width:100%; aspect-ratio:1/1; object-fit:cover;
  box-shadow:0 22px 44px -20px rgba(12,20,60,.4)}
.idea .pic .tape{position:absolute; top:-18px; left:36%; width:140px; transform:rotate(-4deg)}
.idea h2{font-size:clamp(26px,3.2vw,40px)}
.idea .whisper{margin-top:8px}

/* Three moves */
.moves{display:grid; grid-template-columns:repeat(3,1fr); gap:clamp(16px,2.4vw,28px); margin-top:44px}
.move{position:relative; background:#fff; border:2px solid var(--biro); border-radius:22px;
  padding:26px 24px 22px; box-shadow:4px 4px 0 var(--biro); text-align:left}
.move:nth-child(1){transform:rotate(-.6deg)}
.move:nth-child(2){transform:rotate(.5deg) translateY(10px)}
.move:nth-child(3){transform:rotate(-.3deg)}
.move .rank{width:58px; height:58px; margin:-52px 0 12px -8px}
.move .sticker{position:absolute; right:14px; top:-34px; width:66px; height:66px; object-fit:contain; transform:rotate(6deg); z-index:2}
.move h3{padding-right:52px}
.move p{margin:0; color:var(--muted); font-size:16px}

/* Films, taped down like photographs */
.films{display:grid; grid-template-columns:1fr 1fr; gap:clamp(20px,3vw,40px); margin-top:40px}
.film{position:relative; background:#fff; padding:12px 12px 16px; border-radius:6px;
  box-shadow:0 18px 36px -18px rgba(12,20,60,.45), 0 0 0 1px rgba(12,20,112,.08)}
.film:nth-child(1){transform:rotate(-1.2deg)}
.film:nth-child(2){transform:rotate(1deg)}
.film video{width:100%; height:auto; aspect-ratio:660/450; border-radius:3px; background:var(--paper-aged)}
.film .tape{position:absolute; top:-16px; left:50%; width:120px; transform:translateX(-50%) rotate(-3deg)}
.film figcaption{font-family:var(--hand); font-weight:700; font-size:26px; color:var(--biro);
  line-height:1.1; margin:12px 6px 0}
.film figcaption span{display:block; font-family:var(--sans); font-weight:400; font-size:14px; color:var(--muted); margin-top:6px}

/* Feature rows: phones one side, words the other */
.row{display:grid; grid-template-columns:1fr 1fr; gap:clamp(28px,6vw,90px); align-items:center}
.row + .row{margin-top:clamp(64px,8vw,104px)}
.row.rev .media{order:2}
.row .media{display:flex; justify-content:center; gap:clamp(12px,2vw,24px)}
.row .media .phone{width:min(100%,300px)}
.row .media.pair .phone{width:min(47%,270px)}
.row .media.pair .phone:nth-child(2){margin-top:60px}
.row .copy > p{color:var(--muted)}
.row .copy h3{font-size:clamp(22px,2.6vw,30px); margin-bottom:14px}
.row .copy .extra{display:flex; align-items:center; gap:14px; margin-top:18px}
.row .copy .extra img{width:70px; height:auto; transform:rotate(-6deg)}
.row .copy .extra p{margin:0; font-size:14px}

/* A feed, on foil, against GoBe, on paper */
.versus{display:grid; grid-template-columns:1fr 1fr; gap:clamp(16px,3vw,32px); margin-top:40px}
.side{border-radius:24px; padding:30px 28px 20px; text-align:left}
.side h3{font-size:22px}
.side .who{font-family:var(--mono); font-size:12px; font-weight:600; margin:0 0 10px; text-transform:lowercase}
.side ul{list-style:none; padding:0; margin:18px 0 0}
.side li{padding:0 0 12px 30px; position:relative; margin:0}
.side.feed{background:linear-gradient(rgba(248,250,252,.4),rgba(248,250,252,.4)),#c9cbd2 url('foil.jpg') center/520px; color:#1e1f26; box-shadow:inset 0 0 0 1px rgba(0,0,0,.08)}
.side.feed li::before{content:"\\00D7"; position:absolute; left:4px; top:-1px; font-family:var(--mono); color:#5a5c66}
.side.gobe{background:#fff; border:2px solid var(--biro); box-shadow:4px 4px 0 var(--biro)}
.side.gobe li::before{content:""; position:absolute; left:2px; top:9px; width:16px; height:5px;
  background:var(--go); border-radius:3px; transform:rotate(-8deg)}

/* Privacy card and values */
.privacy .two{display:grid; grid-template-columns:.9fr 1.1fr; gap:clamp(24px,5vw,64px); align-items:start}
.privacy .lede{margin-top:10px}
.sheet{background:#fff; border:2px solid var(--biro); border-radius:24px; padding:30px 30px 14px;
  box-shadow:4px 4px 0 var(--biro)}
.sheet p{color:var(--muted)}
.values{display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-top:44px}
.value{border-top:3px solid var(--biro); padding-top:14px}
.value .vtitle{font-family:var(--mono); font-weight:600; font-size:15px; margin-bottom:6px}
.value p{font-size:14px; color:var(--muted); margin:0}

/* Reading it as a business */
.brief .note{max-width:none}
.facts{display:grid; grid-template-columns:1fr 1fr; gap:0 28px; margin:26px 0 18px;
  border-top:2px solid var(--biro)}
.fact{display:flex; justify-content:space-between; gap:18px; padding:12px 0; border-bottom:1px solid var(--line)}
.fact .k{font-family:var(--mono); font-size:12px; font-weight:600; color:var(--biro); text-transform:lowercase; white-space:nowrap}
.fact .v{font-size:15px; text-align:right}

/* The last word, on foil again */
.closer{padding-bottom:clamp(90px,10vw,130px); text-align:center}
.closer .bar{position:relative}
.closer .icon{width:128px; margin:0 auto 22px; filter:drop-shadow(0 18px 28px rgba(12,20,60,.5))}
.closer .lede{margin:0 auto; color:#2a2b33}
.closer h2{font-size:clamp(32px,5vw,58px)}
.closer .btns{display:flex; flex-wrap:wrap; justify-content:center; gap:14px; margin-top:26px}

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
  .hero .bar,.idea .bar,.row,.privacy .two{grid-template-columns:1fr}
  .hero{padding-top:124px}
  .hero-media{width:min(78%,300px); margin-bottom:-90px}
  .hero-media .whisper{display:none}
  .row.rev .media{order:0}
  .moves{grid-template-columns:1fr; gap:34px; margin-top:52px}
  .move:nth-child(n){transform:none}
  .films,.versus{grid-template-columns:1fr}
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
  .hero{padding-top:108px}
  .row .media.pair .phone{width:48%}
  .values{grid-template-columns:1fr}
  .fact{flex-direction:column; gap:2px}
  .fact .v{text-align:left}
  .btn{padding:12px 16px 11px}
}

/* ---------- The collage kit, tucked in ----------
   Small, at the edges, mostly behind the thing it sits by. Nothing here
   carries meaning; it is the scrapbook the app is made of. */
.deco{position:absolute; pointer-events:none; user-select:none; height:auto; z-index:0}
.hero-copy,.idea-copy,.row .media,.row .copy,.move,.film,.side,.sheet,.values,.band > .bar,.closer .bar{position:relative}
.row .copy > :not(.deco),.side > :not(.deco){position:relative; z-index:1}
.phone{z-index:2}
.idea .pic > img:not(.deco):not(.tape){position:relative; z-index:1}
.idea .pic .tape{z-index:3}

.d-hero-sparkle{width:66px; top:-6px; right:4%; transform:rotate(8deg)}
.d-hero-tape{width:118px; top:-18px; right:-34px; transform:rotate(34deg); z-index:4}
.d-hero-steps{width:84px; left:-118px; bottom:10px; transform:rotate(-24deg); opacity:.9}
.d-idea-map{width:170px; right:-54px; bottom:-46px; transform:rotate(9deg)}
.d-idea-compass{width:84px; top:-54px; right:4%; transform:rotate(14deg); opacity:.85}
.d-idea-arrow{width:140px; left:-120px; bottom:-54px; transform:scaleX(-1) rotate(-6deg)}
.ringed{position:relative; white-space:nowrap}
.ringed::after{content:""; position:absolute; left:-12%; right:-12%; top:-38%; bottom:-38%;
  background:url('deco/oval.png') center/100% 100% no-repeat; pointer-events:none}
.d-how-sparkles{width:76px; top:-8px; left:17%; transform:rotate(-8deg)}
.d-move-heart{width:50px; right:-18px; bottom:-24px; transform:rotate(-12deg); z-index:3}
.d-move-sparkle{width:40px; left:-18px; bottom:-18px; transform:rotate(10deg); z-index:3}
.d-film-watch{width:86px; right:-30px; bottom:-34px; transform:rotate(14deg); z-index:3}
.d-film-pin{width:66px; right:-18px; top:-34px; transform:rotate(-10deg); z-index:3}
.d-trails-trainer{width:136px; left:-36px; bottom:-46px; transform:rotate(-12deg); z-index:3}
.d-trails-steps{width:88px; top:-78px; right:14%; transform:rotate(22deg); opacity:.85}
.d-traces-camera{width:118px; left:-40px; bottom:40px; transform:rotate(-12deg); z-index:3}
.d-traces-heart{width:58px; top:-58px; left:-6px; transform:rotate(-10deg)}
.d-sealed-tape{width:132px; top:-20px; left:calc(50% - 66px); transform:rotate(-7deg); z-index:3}
.d-sealed-sparkle{width:62px; top:-52px; right:18%; transform:rotate(12deg)}
.d-band-stamp{width:104px; left:1%; bottom:-58px; transform:rotate(-12deg)}
.d-band-cd{width:118px; right:-7%; top:-96px; transform:rotate(18deg)}
.d-around-coffee{width:84px; right:-26px; bottom:-22px; transform:rotate(10deg); z-index:3}
.d-around-map{width:108px; top:-66px; right:4%; transform:rotate(9deg)}
.d-around-bike{width:150px; left:-8px; bottom:-120px; transform:rotate(-4deg); opacity:.95}
.d-board-rosette{width:94px; top:-28px; right:16%; transform:rotate(12deg); z-index:3}
.d-board-star{width:50px; top:-54px; left:-6px; transform:rotate(-12deg)}
.d-friends-phone{width:70px; left:10%; bottom:-6px; transform:rotate(-16deg); z-index:3}
.d-friends-speech{width:72px; left:2%; bottom:88px; transform:rotate(8deg); z-index:3}
.d-friends-smiley{width:64px; top:-64px; right:22%; transform:rotate(10deg)}
.d-feed-cursor{width:78px; right:-14px; top:-34px; transform:rotate(-10deg); z-index:2}
.d-gobe-steps{width:70px; right:12px; bottom:-28px; transform:rotate(18deg); z-index:2}
.d-privacy-receipt{width:108px; right:-44px; top:-54px; transform:rotate(14deg); z-index:-1}
.d-values-globe{width:70px; right:-6px; top:-72px; transform:rotate(12deg); opacity:.8}
.d-brief-signpost{width:84px; right:3%; top:6px; transform:rotate(6deg)}
.d-closer-globe{width:84px; left:12%; top:0; transform:rotate(-14deg)}
.d-closer-sparkle{width:62px; right:18%; top:10px; transform:rotate(10deg)}
.d-closer-cd{width:124px; right:5%; bottom:-40px; transform:rotate(22deg)}
.brief h2{display:inline-block; position:relative}
.brief h2::after{content:""; position:absolute; left:-2%; right:-6%; bottom:-16px; height:18px;
  background:url('deco/underline.png') center/100% 100% no-repeat}
main.col h1::after{content:""; display:inline-block; width:.62em; height:.62em; margin-left:.28em;
  background:url('deco/star.png') center/contain no-repeat; transform:rotate(12deg) translateY(-.12em)}
.handoff-mark{position:relative; display:inline-block}
.handoff-mark::after{content:""; position:absolute; width:96px; height:34px; top:-12px; right:-38px;
  background:url('deco/tape.png') center/contain no-repeat; transform:rotate(30deg)}

@media (max-width:900px){
  .deco{display:none}
  .deco.keep{display:block}
  .d-hero-tape{width:92px; right:-20px}
  .d-hero-sparkle{width:48px; right:2%; top:-18px}
  .d-idea-map{width:120px; right:-14px; bottom:-30px}
  .d-trails-trainer{width:100px; left:-6px; bottom:-30px}
  .d-traces-camera{width:90px; left:-6px}
  .d-around-coffee{width:66px; right:-6px}
  .d-board-rosette{width:74px}
  .d-film-watch{width:66px; right:-10px}
  .d-film-pin{width:52px; right:-6px}
  .d-band-stamp{width:80px}
  .d-closer-globe{width:64px; left:6%}
  .d-closer-sparkle{width:48px; right:8%}
  .d-gobe-steps{width:56px}
  .d-friends-phone{width:56px; left:6%}
}


/* ---------- Handwritten notes on the screenshots ---------- */
.callout{position:absolute; margin:0; z-index:5; pointer-events:none; white-space:nowrap;
  font-family:var(--hand); font-weight:700; font-size:25px; line-height:1.02; color:var(--biro)}
.callout img{position:absolute; width:104px; height:auto}
.c-hero-sealed{right:-212px; top:86px; transform:rotate(-3deg)}
.c-hero-sealed img{left:-104px; top:14px; transform:scaleX(-1) rotate(14deg)}
.c-hero-walk{left:-226px; top:372px; text-align:right; transform:rotate(-4deg)}
.c-hero-walk img{right:-104px; top:20px; transform:rotate(-8deg)}
.c-trail{right:2%; bottom:-58px; transform:rotate(-3deg)}
.c-trail img{left:-100px; top:-26px; transform:scaleX(-1) rotate(-28deg)}
.c-trace{left:6%; bottom:-60px; transform:rotate(3deg)}
.c-trace img{right:-104px; top:-18px; transform:rotate(-30deg)}

/* ---------- Sealed, on foil ---------- */
.sealed-band .copy p{color:#26272e}
.sealed-band .copy .extra p{color:#26272e}

/* ---------- The GoBe Score receipt ---------- */
.receipt{position:relative; background:#fff; width:min(100%,360px); margin:24px 0 16px;
  padding:22px 22px 16px; font-family:var(--mono); font-size:13px; color:var(--ink);
  box-shadow:0 16px 30px -18px rgba(12,20,60,.45); transform:rotate(-1.4deg)}
.receipt::before,.receipt::after{content:""; position:absolute; left:0; right:0; height:10px;
  background:linear-gradient(135deg,#fff 25%,transparent 25%) -6px 0/12px 12px repeat-x,
    linear-gradient(225deg,#fff 25%,transparent 25%) -6px 0/12px 12px repeat-x}
.receipt::after{bottom:-10px}
.receipt::before{top:-10px; transform:rotate(180deg)}
.r-head{font-weight:600; font-size:15px; text-align:center; margin:0; letter-spacing:.06em; text-transform:uppercase}
.r-sub{text-align:center; margin:2px 0 0; color:var(--faint); font-size:11.5px}
.receipt ul{list-style:none; padding:0; margin:14px 0 6px; border-top:1.5px dashed rgba(12,20,112,.35)}
.receipt li{display:flex; justify-content:space-between; gap:12px; margin:0; padding:8px 0;
  border-bottom:1px dashed rgba(12,20,112,.2)}
.receipt li b{color:var(--go-dark); font-weight:600}
.r-foot{font-family:var(--hand); font-weight:700; font-size:23px; color:var(--biro); text-align:center; margin:8px 0 0}

/* ---------- The invite link, as the app draws it ---------- */
.linkpill{display:inline-block; font-family:var(--mono); font-size:14px; font-weight:600; color:var(--ink);
  background:var(--go-glow); border:2px solid var(--biro); border-radius:14px; padding:12px 18px 11px;
  box-shadow:3px 3px 0 var(--biro); margin-top:6px; transform:rotate(-1deg)}
.linkpill span{color:var(--biro)}

/* ---------- A Windows 98 window, gone over in biro ---------- */
.win{position:relative; max-width:900px; margin:0 auto; background:#fff; border:2px solid var(--biro); border-radius:10px;
  box-shadow:5px 5px 0 var(--biro); overflow:hidden}
.win-bar{display:flex; align-items:center; gap:7px; background:var(--biro); color:#fff;
  font-family:var(--mono); font-size:12px; font-weight:600; padding:8px 12px}
.win-bar span{flex:1}
.win-bar i{display:inline-block; width:17px; height:15px; border:1.5px solid #fff; border-radius:3px}
.win-body{padding:28px 32px 20px}
.brief .win-body > p{color:var(--muted); max-width:44em}
.d-brief-signpost{z-index:3; right:max(1%, calc(50% - 540px)) !important; top:-34px !important}

@media (max-width:1180px){ .callout{display:none} }
@media (max-width:560px){ .win-body{padding:22px 18px 14px} .receipt{width:100%} }

@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  .btn,nav.top a.get{transition:none}
}
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
HOME_TITLE = "The social network on a map"
HOME_DESC = (
    "GoBe is the social network on a map. Press play and walk, leave traces where you stood, "
    "and find what people have left round here. Free on iPhone."
)

home = f"""<section class="hero foil torn-below">
<div class="bar">
<div class="hero-copy">
{deco('sparkle','d-hero-sparkle', keep=True)}
<p class="eyebrow">The social network on a map</p>
<h1>Go beyond the screen.</h1>
<p class="lede">Press play and walk. The fog lifts behind you, and the <strong>traces</strong>
people left round here turn up underneath.</p>
<div class="btns">
<a class="btn primary" href="{APP_STORE_URL}">Download on the App Store</a>
<a class="btn" href="#how">How it works</a>
</div>
<p class="note">Free on iPhone · Made in the UK · Ages 16+</p>
</div>
<div class="hero-media">
<p class="callout c-hero-sealed">sealed. walk over<br>and see.<img src="assets/deco/arrow.png" alt="" width="320" height="75"></p>
<p class="callout c-hero-walk"><img src="assets/deco/arrow.png" alt="" width="320" height="75">the fog lifts<br>where you walk.</p>
{deco('tape','d-hero-tape', keep=True)}
{deco('green-steps','d-hero-steps')}
<div class="phone"><img src="assets/screens/fog-walk.jpg" width="720" height="1564"
  alt="The GoBe map of Soho under iridescent foil, torn open along a walk, with a green trail running through the cleared streets"></div>
</div>
</div>
</section>

<section class="band idea">
<div class="bar">
<div class="pic">
<img class="tape" src="assets/tape.png" alt="" width="220" height="80">
{deco('map-scrap','d-idea-map', keep=True)}
<img src="assets/cut-through.jpg" width="1100" height="1100" loading="lazy"
  alt="A green route and a blue dot on a paper map, showing through a tear in crumpled holographic foil">
</div>
<div class="idea-copy">
{deco('compass','d-idea-compass')}
<p class="eyebrow">The idea</p>
<h2>Your phone shows you everywhere. GoBe shows you here.</h2>
<p class="lede">Every trace is pinned to the spot it was left, and the only way to read one
is to go there. Your map starts under fog, and you clear it <span class="ringed">on foot</span>.</p>
<p class="lede">Cross paths with someone and, if you've both said yes, GoBe tells you.</p>
<span class="whisper">you have to go outside to cut through it.</span>
</div>
</div>
</section>

<section class="band tight center" id="how">
<div class="bar">
{deco('green-sparkles','d-how-sparkles')}
<p class="eyebrow">How it works</p>
<h2>Walk. Leave a trace. Go and find one.</h2>
<p class="lede">Three things. That's the app.</p>
<div class="moves">
<div class="move">
<img class="rank" src="assets/rank-1.png" alt="1" width="120" height="120">
{deco('blue-sparkle','d-move-sparkle')}
<img class="sticker" src="assets/play.png" alt="" width="325" height="311">
<h3>Press play and walk</h3>
<p>GoBe draws your route as a <span class="word">trail</span> and the fog lifts behind you.
What you clear stays clear all day.</p>
</div>
<div class="move">
<img class="rank" src="assets/rank-2.png" alt="2" width="120" height="120">
{deco('pixel-heart','d-move-heart')}
<img class="sticker" src="assets/plus.png" alt="" width="325" height="311">
<h3>Leave a trace</h3>
<p>Write a line, snap a photo or film something. Your <span class="word">trace</span> sits on
the spot for whoever comes along next.</p>
</div>
<div class="move">
<img class="rank" src="assets/rank-3.png" alt="3" width="120" height="120">
<img class="sticker" src="assets/sealed.png" alt="" width="240" height="240">
<h3>Go there to read it</h3>
<p>Traces further off glow under the fog. Walk up to one and it opens. You have to
<span class="word">turn up</span>.</p>
</div>
</div>

<div class="films">
<figure class="film">
<img class="tape" src="assets/tape.png" alt="" width="220" height="80">
{deco('stopwatch','d-film-watch', keep=True)}
<video src="assets/films/walk.mp4" poster="assets/films/walk.jpg" width="660" height="450"
  autoplay muted loop playsinline preload="metadata" aria-label="A walk along Whitehall, the fog lifting behind the walker"></video>
<figcaption>the fog lifts as you walk.<span>What you clear stays clear all day. Tomorrow it rolls back in, so off you go again.</span></figcaption>
</figure>
<figure class="film">
<img class="tape" src="assets/tape.png" alt="" width="220" height="80">
{deco('pin','d-film-pin', keep=True)}
<video src="assets/films/trace.mp4" poster="assets/films/trace.jpg" width="660" height="450"
  autoplay muted loop playsinline preload="metadata" aria-label="A trace left on the map, holding the fog back round it as likes arrive"></video>
<figcaption>a trace holds its ground.<span>Every like, comment and retrace pushes the fog further back round it.</span></figcaption>
</figure>
</div>
</div>
</section>

<section class="band">
<div class="bar">
<div class="row">
<div class="media pair">
{deco('trainer','d-trails-trainer', keep=True)}
<div class="phone"><img src="assets/screens/walk.jpg" width="720" height="1564" loading="lazy"
  alt="A GoBe trail being recorded through Soho, the walked route drawn in green"></div>
<div class="phone"><img src="assets/screens/trail.jpg" width="720" height="1564" loading="lazy"
  alt="A finished GoBe trail, with the route on a map, the distance travelled and the time spent outside"></div>
<p class="callout c-trail"><img src="assets/deco/arrow.png" alt="" width="320" height="75">name it. keep it.</p>
</div>
<div class="copy">
{deco('steps','d-trails-steps')}
<p class="eyebrow">Trails</p>
<h3>Press play. Press it again to keep it.</h3>
<p>Your route draws itself across the map while you walk, for up to twelve hours. Stop and
you keep the lot: the line, the distance, the time outside and every trace you left on the way.</p>
<p>Switch location off halfway and the trail's binned. Only real walks count.</p>
</div>
</div>

<div class="row rev">
<div class="media pair">
{deco('camera','d-traces-camera', keep=True)}
<div class="phone"><img src="assets/screens/compose.jpg" width="720" height="1564" loading="lazy"
  alt="Leaving a trace in GoBe: a short note being written on a card pinned to the spot"></div>
<div class="phone"><img src="assets/screens/trace.jpg" width="720" height="1564" loading="lazy"
  alt="A trace opened in GoBe, reading &quot;They've put the tables out on the pavement again&quot;"></div>
<p class="callout c-trace">someone<br>stood here.<img src="assets/deco/arrow.png" alt="" width="320" height="75"></p>
</div>
<div class="copy">
{deco('heart','d-traces-heart')}
<p class="eyebrow">Traces</p>
<h3>Leave a trace where you stood.</h3>
<p>A tip, a thought, a photo of whatever's happening right there. It stays on that spot for
whoever comes along next, and they can like it, comment and retrace it onto their own map.</p>
<p>The more it's liked, the further it reaches. Your street, written by the people on it.</p>
</div>
</div>
</div>
</section>

<section class="band foil torn-above torn-below sealed-band">
<div class="bar">
<div class="row">
<div class="media">
{deco('holo-tape','d-sealed-tape', keep=True)}
<div class="phone"><img src="assets/screens/sealed.jpg" width="720" height="1564" loading="lazy"
  alt="The GoBe drawer, where traces beyond a short walk are dealt wrapped in iridescent foil"></div>
</div>
<div class="copy">
{deco('sparkle-small','d-sealed-sparkle')}
<p class="eyebrow">Sealed</p>
<h3>Far-off traces stay sealed till you get there.</h3>
<p>On the map they glow under the fog in their own colour: blue for a trace, yellow for a
place, green for a community. In the drawer they come wrapped in foil.</p>
<p>Tap one and GoBe tells you how many minutes away it is. Walk there and it opens.</p>
<div class="extra"><img src="assets/sealed.png" alt="" width="240" height="240">
<p>Who left it and what it says: that's what the walk is for.</p></div>
</div>
</div>
</div>
</section>

<section class="band">
<div class="bar">
<div class="row rev">
<div class="media pair">
{deco('coffee','d-around-coffee', keep=True)}
<div class="phone"><img src="assets/screens/map.jpg" width="720" height="1564" loading="lazy"
  alt="The GoBe map of central London with traces, places and events laid on the streets"></div>
<div class="phone"><img src="assets/screens/event.jpg" width="720" height="1564" loading="lazy"
  alt="An event board in GoBe, Records in the Square, with Going, Maybe and Can't go"></div>
</div>
<div class="copy">
{deco('folded-map','d-around-map')}
{deco('bicycle','d-around-bike')}
<p class="eyebrow">What's around you</p>
<h3>Everything round here lives on the map.</h3>
<p>Cafés, parks, gyms, bookshops and bars sit between the traces. Communities and events are
pinned where they meet.</p>
<p>Say you're going, turn up, and leave a trace while you're there.</p>
</div>
</div>

<div class="row score">
<div class="media">
{deco('rosette','d-board-rosette', keep=True)}
<div class="phone"><img src="assets/screens/board.jpg" width="720" height="1564" loading="lazy"
  alt="GoBe's leaderboard for Westminster: who's around, ranked, with the reader fourth"></div>
</div>
<div class="copy">
{deco('star','d-board-star')}
<p class="eyebrow">Your ground</p>
<h3>Everything you do out there counts.</h3>
<p>Your GoBe Score goes up every time you get out. Your area has a board too, ranking who's
put the most into it: your neighbourhood, your borough, your city.</p>
<div class="receipt" aria-label="What earns GoBe Score points">
<p class="r-head">GoBe Score</p>
<p class="r-sub">what counts</p>
<ul>
<li><span>Trace left</span><b>+10</b></li>
<li><span>Trail kept</span><b>+20</b></li>
<li><span>Every 500 steps</span><b>+1</b></li>
<li><span>Reached someone's trace</span><b>+12</b></li>
<li><span>Someone retraced yours</span><b>+8</b></li>
<li><span>Friend added</span><b>+15</b></li>
<li><span>Your friend's first trace</span><b>+50</b></li>
</ul>
<p class="r-foot">get out more. climb higher.</p>
</div>
</div>
</div>

<div class="row rev friends">
<div class="media">
{deco('flip-phone','d-friends-phone', keep=True)}
{deco('pixel-speech','d-friends-speech')}
<div class="phone"><img src="assets/screens/invite.jpg" width="720" height="1564" loading="lazy"
  alt="GoBe's invite page, with a personal link to share with friends"></div>
</div>
<div class="copy">
{deco('smiley','d-friends-smiley')}
<p class="eyebrow">Friends</p>
<h3>GoBe's better with your people.</h3>
<p>Your invite code lets three people in, so pick them well. They get 25 points for joining,
and you get 50 when they leave their first trace.</p>
<p class="linkpill">gobeapp.co.uk/f/?c=<span>YOURCODE</span></p>
</div>
</div>
</div>
</section>

<section class="band tight">
<div class="bar center">
<p class="eyebrow">A feed, and GoBe</p>
<h2>A feed keeps you scrolling. GoBe gets you out.</h2>
<div class="versus">
<div class="side feed">
{deco('cursor','d-feed-cursor')}
<p class="who">A feed</p>
<h3>Keeps you in</h3>
<ul>
<li>An algorithm picks what you see</li>
<li>Posts from everywhere, all at once</li>
<li>Built to keep you scrolling</li>
<li>Ends on the screen</li>
</ul>
</div>
<div class="side gobe">
{deco('green-steps','d-gobe-steps', keep=True)}
<p class="who">GoBe</p>
<h3>Gets you out</h3>
<ul>
<li>Distance decides what you see</li>
<li>What was left here, for whoever gets here</li>
<li>Built to get you somewhere</li>
<li>Ends outside, round here, with people from here</li>
</ul>
</div>
</div>
</div>
</section>

<section class="band privacy">
<div class="bar two">
<div>
<p class="eyebrow">Privacy</p>
<h2>Your exact location stays off the map.</h2>
<p class="lede">A map of real places has to keep people safe at them. Here's how GoBe does it.</p>
</div>
<div class="sheet">
{deco('receipt','d-privacy-receipt')}
<p>Traces are saved to a rough spot on a grid about thirty metres across. The exact point is
never stored, on your phone or on our servers.</p>
<p>Trails are more precise, so trails stay private to you.</p>
<p>Mark home, work or anywhere else as protected and GoBe keeps traces out of it. Protected
areas stay on your phone.</p>
<p>GoBe is free, carries no ads and never sells your data. The detail is in the
<a href="privacy.html">Privacy Policy</a>.</p>
</div>
</div>
<div class="bar">
<div class="values">
{deco('globe','d-values-globe')}
<div class="value"><div class="vtitle">Free</div><p>Nothing to pay and no ads.</p></div>
<div class="value"><div class="vtitle">Your data is yours</div><p>We never sell it. Delete your account and everything in it whenever you like.</p></div>
<div class="value"><div class="vtitle">Made in the UK</div><p>An independent app, made in Britain.</p></div>
<div class="value"><div class="vtitle">16 and over</div><p>Younger users start on stricter privacy settings.</p></div>
</div>
</div>
</section>

<section class="band tight brief" id="about">
<div class="bar">
{deco('signpost','d-brief-signpost')}
<div class="win">
<div class="win-bar"><span>about-gobe.txt</span><i></i><i></i><i></i></div>
<div class="win-body">
<p class="eyebrow">For investors, partners and press</p>
<h2>The short version.</h2>
<p>Social networks got very good at keeping people on their phones. GoBe is built to get them
out of the house. You post by standing somewhere, you see what's near you, and the app is
working when somebody goes out.</p>
<p>The map is the moat. It's filled in street by street by the people who walk them, it can't
be copied into another city, and every trace makes it more useful to everyone nearby. GoBe
grows the way a place does, one street at a time.</p>
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

<section class="closer foil torn-above">
<div class="bar">
{deco('pixel-globe','d-closer-globe', keep=True)}
{deco('sparkle','d-closer-sparkle', keep=True)}
{deco('cd','d-closer-cd')}
<img class="icon" src="assets/icon-rounded.png" alt="" width="240" height="240">
<h2>See you out there.</h2>
<p class="lede">GoBe is free on the App Store for iPhone.</p>
<div class="btns">
<a class="btn primary" href="{APP_STORE_URL}">Download on the App Store</a>
<a class="btn" href="support.html">Support</a>
</div>
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

# --- /f/ : a friend's invite code ------------------------------------------
#
# Where a friend's invite link lands (/f/?c=CODE). It is how GoBe is
# downloaded from an invite: the code is shown big, the App Store button
# copies it on the way out (a tap is the only moment a page may write to the
# clipboard), and the sign-up page's code field has a Paste button for it.
# If GoBe is already on the phone, the universal link opens the app instead
# (the association file claims /f/), and the app fills the code in itself.
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
        var go = function () {{ location.href = STORE; }};
        navigator.clipboard.writeText(code).then(go, go);
      }});
    }}
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
<p class="note">Get GoBe copies it for you. When you make your account, tap
<strong>Paste</strong> by the invite code: it puts points on your GoBe Score
straight away, and on theirs once you leave your first trace.</p>
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
