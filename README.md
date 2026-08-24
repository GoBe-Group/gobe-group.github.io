# GoBe — legal & support site

The public site for the GoBe iOS app, live at **https://gobeapp.co.uk**.

Deployed to **Cloudflare Workers static assets** (project `gobe`) on every push
to `main`; see `wrangler.jsonc`. The repo name predates the domain. GitHub Pages
still serves the old `gobe-group.github.io` URL and should stay switched on —
profile links shared before the move point there.

Note Workers serves pages without the `.html` suffix: `/privacy.html` 307s to
`/privacy`. Use the clean form anywhere a URL is recorded (App Store Connect).

- `privacy.html` — Privacy Policy (App Store "Privacy Policy URL")
- `terms.html` — Terms of Service
- `support.html` — Support & contact (App Store "Support URL")
- `index.html` — landing page. It exists to make one argument, in this order:
  what GoBe is (a social network on a map rather than in a feed), the three
  moves it is made of (walk a trail, leave a trace, be found there), what those
  moves add up to (people whose paths cross, and a neighbourhood built by the
  people in it), why that is not a feed, and how it stays safe. A visitor who
  reads only the hero and the line under it should still be able to say what the
  app does; that is the test the page has to pass, and the reason the sections
  are ordered the way they are rather than by feature. The last band is written
  for someone reading the site as a business, and carries the contact address.
  All of it is generated from the `home` block in `build.py`, **not** edited
  here — see the warning below.
- `u/index.html` — where a shared profile link
  (`/u/?h=<handle>`) lands when iOS didn't hand it to the app. Shows no profile
  data by design, only a way into the app: it fires `gobe://u/?h=<handle>` to
  reach an installed GoBe, and if the page is still open ~1.4s later (nothing
  took the scheme, so the app isn't there) it goes to the App Store product
  page. `?noauto=1` turns the automatic attempt off for looking at the page.
- `404.html` — ordinary "not found", except for the old pretty profile links
  (`/u/ada`), which have no file behind them and are redirected to `/u/?h=ada`.
  `wrangler.jsonc` sets `not_found_handling: "404-page"` so Workers serves it.
- `.well-known/apple-app-site-association` — claims `/u/` for the GoBe app so
  iOS opens profile links in-app. Generated; edit `APP_ID` in `build.py` if the
  Team ID or bundle id ever changes.
- `_headers` — serves that file as `application/json`, which Apple requires and
  GitHub Pages could not do. This is why the site moved hosts.
- `.assetsignore` — keeps `build.py` and the source markdown out of the upload;
  `wrangler.jsonc` points the asset directory at the repo root.

`/u/` and `404.html` are the only pages carrying a script, and it's inline and
pinned by a `sha256` CSP hash that `build.py` computes from the script itself,
so the hash can't drift and nothing external can ever load. Every other page
keeps the site's script-free `default-src 'none'` policy.

**Universal links need Apple's CDN, not just this site.** iOS reads the
association from `app-site-association.cdn-apple.com/a/v1/gobeapp.co.uk`, not
from the origin, and that copy appears only once Apple has crawled the domain.
Until it does, universal links silently do nothing however correct the file is —
which is what the `gobe://` fallback above is for. Check it with:

```
curl -sI https://app-site-association.cdn-apple.com/a/v1/gobeapp.co.uk
```

The `/u/` link deliberately carries the handle as a query (`?h=`) rather than a
path (`/u/ada`), a constraint inherited from GitHub Pages, which could only
serve real files — a path form would have 404'd, losing both the 200 status and
the link preview. The app still parses the path form, for links shared before
this changed.

## Everything here is generated: edit `build.py`, never the output

**`build.py` writes every `.html` file and `assets/style.css`.** Editing those
directly appears to work and is then silently thrown away by the next
`python3 build.py`, which is a genuinely easy hour to lose. The page copy lives
in the `home` / `support` blocks of `build.py`; the stylesheet lives in the
`CSS` constant at the top of it. The only hand-maintained sources in the repo
are the two legal markdown files and the images under `assets/`.

`privacy.html` and `terms.html` are generated from `gobe-privacy-policy.md` and
`gobe-terms-of-service.md`, which are kept word-for-word in sync with the in-app
Swift docs. After editing a `.md` file, or anything in `build.py`, regenerate
with:

```
python3 build.py
```

then commit and push.

## Screenshots

`assets/screens/*.jpg` are exported at 720 px wide from full-resolution
simulator captures, and the capture is a rig rather than a photo session:
`GoBeUITests/AppStoreScreenshots.swift` in the app repo drives the App Store
scenes, and `GoBeUITests/WebsiteScreenshots.swift` drives the two this site
needs that the store listing never wanted (the areas standings, and the map of
what is around you). Both run only when their env flag is set:

```
TEST_RUNNER_CAPTURE_WEBSITE_SCREENSHOTS=1 xcodebuild test -project GoBe.xcodeproj -scheme GoBe -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -parallel-testing-enabled NO -only-testing:GoBeUITests/WebsiteScreenshotCapture
```

Pass `-parallel-testing-enabled NO`: the clones a parallel run makes fight over
the simulator and turn a readable failure into a wedged one. The attachments
come out of the `.xcresult` bundle.
