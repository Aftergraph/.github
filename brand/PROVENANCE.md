# Provenance: `.github/brand/` tree

- Canonical Brand OS source: `Aftergraph/brand`, version `1.1.0`
  (PR `Aftergraph/brand#20` merged as `8a1f878`; release `v1.1.0`,
  tarball SHA-256 `3d881b90…bd6f8f` — see
  `AFTERGRAPH-BRAND-ADOPTION-MATRIX.md`).
- This `brand/` tree is a **deployed copy**, not a canonical source.
  Its "One source of truth: `brand/master/*.svg`" claim is superseded.
- Local exports under `brand/exports/`, `brand/github/`, `brand/apps/`, and
  `brand/marketplace/` are retained until they are regenerated from the
  canonical release and their consumers are migrated. Do not delete them first.
- Competing sources flagged for removal after consumer migration:
  - `brand/tokens.json` (superseded by `@aftergraph/brand` `tokens.json` /
    `tokens.css` v1.1.0 state aliases).
  - `brand/manifest.json` v1.0.0 (superseded by the capability-aware
    `brand-assets` schema v2 in `Aftergraph/brand/schemas/`).
  - Legacy `altName: ABDE Intelligence` in `brand/manifest.json` is
    provenance-only; current masterbrand is Aftergraph alone.
- Sentinel assets, if any appear here, stay blocked per
  `Aftergraph/brand#19` and `Aftergraph/sentinel#7`.
