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
  (`/u/?h=<handle>`) lands when the GoBe app isn't installed to catch it. Shows
  no profile data by design, only a way into the app.
- `.well-known/apple-app-site-association` — claims `/u/` for the GoBe app so
  iOS opens profile links in-app. Generated; edit `APP_ID` in `build.py` if the
  Team ID or bundle id ever changes.
- `_headers` — serves that file as `application/json`, which Apple requires and
  GitHub Pages could not do. This is why the site moved hosts.
- `.assetsignore` — keeps `build.py` and the source markdown out of the upload;
  `wrangler.jsonc` points the asset directory at the repo root.

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
