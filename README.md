# Chabad Historical Map

Interactive web app showing the geographic and temporal history of Chabad-Lubavitch chassidic figures, from the Baal Shem Tov era to the present.

Inspired by [theacharonim.com](https://theacharonim.com/), focused specifically on Chabad.

## Status

In development. Data is seeded (82 figures, 58 places); the app is being built.

## Three views

- **Map** — birth and death places of each figure, plotted geographically
- **Timeline** — lifespans laid out chronologically, color-coded by generation
- **Person page** — bilingual (Hebrew + English) details for each figure

## Quick start

If you're a developer picking this up, **read `CLAUDE.md` first** — it has the full project context.

```bash
# After the app is scaffolded:
cd app
npm install
npm run dev
```

## Adding more figures

The seeded dataset is a starting point, not a comprehensive list. To add figures from chassidic source books, see `docs/notebooklm-prompts.md` for an extraction workflow using NotebookLM.

## Repository layout

```
data/                  # Seeded person and place records
docs/                  # Schema specs and extraction workflow
app/                   # The web app (in progress)
CLAUDE.md              # Project context for AI-assisted development
```

## Schema

Two entities — `person` and `place` — kept intentionally minimal. See `docs/spec.md` for the full schema. Forward-compatible with the larger schema in `docs/full-spec-future.md` for when the project grows.
