# GoBe — legal & support site

Public pages served at GitHub Pages for the GoBe iOS app.

- `privacy.html` — Privacy Policy (App Store "Privacy Policy URL")
- `terms.html` — Terms of Service
- `support.html` — Support & contact (App Store "Support URL")
- `index.html` — landing page

`privacy.html` and `terms.html` are generated from `gobe-privacy-policy.md` and
`gobe-terms-of-service.md`, which are kept word-for-word in sync with the in-app
Swift docs. After editing a `.md` file, regenerate with:

```
python3 build.py
```

then commit and push.
