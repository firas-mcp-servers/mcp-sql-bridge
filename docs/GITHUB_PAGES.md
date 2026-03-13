# Landing page: GitHub Pages or Vercel

This document describes how to publish the MkDocs documentation site as a public landing page.

---

## Option A — GitHub Pages (recommended, free, zero config)

### One-time setup

1. Go to **Settings → Pages** in the GitHub repo.
2. Set **Source** to `GitHub Actions`.
3. Add the workflow below as `.github/workflows/pages.yml`.

### Workflow

Create `.github/workflows/pages.yml`:

```yaml
name: Deploy docs to GitHub Pages

on:
  push:
    branches: [ main, master ]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Poetry
        uses: abatilo/actions-poetry@v3
        with:
          poetry-version: "2.0.0"

      - name: Install deps (web group for mkdocs)
        run: poetry install --with web

      - name: Build docs
        run: poetry run mkdocs build --strict

      - uses: actions/upload-pages-artifact@v3
        with:
          path: site/

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

After merging, the docs are published at:
`https://firas-mcp-servers.github.io/mcp-sql-bridge/`

---

## Option B — Vercel

1. Import the repo at https://vercel.com/new.
2. Set **Framework Preset** to "Other".
3. Set **Build Command**: `pip install mkdocs-material && mkdocs build`
4. Set **Output Directory**: `site`
5. Deploy. Vercel auto-deploys on every push to `main`.

---

## Custom domain (optional)

Add a `CNAME` file to `docs/` with your domain (e.g. `mcp-sql-bridge.dev`), and configure the DNS CNAME record to point to `firas-mcp-servers.github.io`.
