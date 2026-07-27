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
- `index.html` — landing page
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

`privacy.html` and `terms.html` are generated from `gobe-privacy-policy.md` and
`gobe-terms-of-service.md`, which are kept word-for-word in sync with the in-app
Swift docs. After editing a `.md` file, regenerate with:

```
python3 build.py
```

then commit and push.
