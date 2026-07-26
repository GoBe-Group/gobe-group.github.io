# GoBe — legal & support site

Public pages served at GitHub Pages for the GoBe iOS app.

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

The `/u/` link deliberately carries the handle as a query (`?h=`) rather than a
path (`/u/ada`). GitHub Pages can only serve real files, so a path form would
404 — losing both the 200 status and the link preview. The app still parses the
path form, for links shared before this changed.

`privacy.html` and `terms.html` are generated from `gobe-privacy-policy.md` and
`gobe-terms-of-service.md`, which are kept word-for-word in sync with the in-app
Swift docs. After editing a `.md` file, regenerate with:

```
python3 build.py
```

then commit and push.
