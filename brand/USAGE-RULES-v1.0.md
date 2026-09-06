# Aftergraph Brand Usage Rules v1.0

> Status: **provisional-not-trademark-cleared**. Visual identity rules for the
> Aftergraph / ABDE Intelligence institutional graph brand. Part of the Brand OS
> master kit; canonical sources live in `brand/master/`.

## 1. Safe area (clear space)

- The mark requires clear space on all sides equal to **the height of one node
  ring** (≈ 12.5% of the mark's width).
- No text, logos, or visual noise may intrude into the safe area.
- For the lockups, safe area = **half the x-height of the wordmark** on all sides.

## 2. Minimum sizes

- Mark (digital): **24 px** width minimum; below that use the icon.
- Wordmark lockup: **120 px** width minimum.
- Stacked lockup: **64 px** width minimum.
- GitHub avatar: always use the `aftergraph-avatar.png` 512 export; never let a
  browser downscale the master mark below 24 px in a context that must stay
  legible.
- Print: mark ≥ **8 mm**; lockup ≥ **25 mm**.

## 3. Contrast rules

- The mark's default is `control-cyan` (#42C7E8) on `graph-midnight` (#0E1630)
  or `institution-black` (#080C14).
- On light backgrounds use `aftergraph-mark-light.svg` variants; on dark
  backgrounds use the standard mark.
- Minimum contrast for text adjacent to the mark: WCAG AA (4.5:1) for body,
  3:1 for large display text.
- Never place the cyan mark on a mid-tone background where contrast falls under
  3:1 against the nearest node.

## 4. Logo misuse rules

The mark may be:

- scaled proportionally only (never stretched or squashed)
- recolored only via the token palette
- rotated only in the canonical orientations (0/90/180/270)

The mark may NOT be:

- placed on a busy photographic background without a scrim
- given drop shadows, glows, or gradients
- combined with another logo to imply partnership without governance approval
- used as a generic "AI" icon, or as a favicon without the favicon export
- used in a sentence as a bullet or decorative glyph
- used to imply trademark status (it is provisional)

## 5. Export rules

- All exports derive from the SVG masters in `brand/master/` (single source of
  truth). Never hand-edit a PNG.
- Avatar/icon exports: 512×512 transparent PNG; 1024×1024 master; 200×200 min.
- Social preview: 1280×640 PNG, < 1 MB, legible at thumbnail size, free of fake
  runtime status or unverifiable claims.
- Hero: 1600×900 WebP (dark + light), with PNG fallback for READMEs.
- Diagram family: SVG with `role="img"` and an `aria-label`; text must be
  real text nodes (never outlined-to-paths for accessibility).
- Screenshots: real product captures only; 1200+ px wide; record source
  revision + date in the asset registry. AI-generated/edited UI may only be
  concept material, never evidence.

## 6. Governance

- The `.github/brand/` kit is canonical. Product repos consume exports, not
  independent redesigns.
- Any change to `brand/master/` or `tokens.json` requires a PR reviewed against
  this rule set.
- A shared visual grammar does not imply shared claim inheritance: runtime,
  execution, conformance, and scientific evidence remain separate boundaries.