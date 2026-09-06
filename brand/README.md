# Aftergraph Brand OS — Master Kit

> Canonical visual identity for the Aftergraph / ABDE Intelligence institutional
> graph. **Status: provisional — not trademark-cleared.**

## What lives here

| Path | Contents |
|---|---|
| `master/` | Canonical SVG masters: mark, mono, inverse, wordmarks, lockups |
| `exports/` | PNG/ICO exports derived from masters (avatar, favicons, sizes) |
| `github/` | Org-level GitHub assets (hero, social preview) |
| `apps/` | GitHub App mark/badge sources (no app asserted) |
| `marketplace/` | Marketplace dimension kit (no listing asserted) |
| `teams/` | Six team identity families (512 SVG + PNG) |
| `templates/` | Release + repo-social-preview templates |
| `tokens.json` | Canonical color/typography/grammar tokens |
| `USAGE-RULES-v1.0.md` | Safe area, min size, contrast, misuse, export, governance |
| `GITHUB-VISUAL-ASSET-STANDARD-v1.0.md` | Per-surface asset contract |
| `BADGE-POLICY-v1.0.md` | Dynamic badge rules |

## Governing rules

- **One source of truth**: `brand/master/*.svg` are canonical. All PNGs/WebPs
  everywhere are derived.
- **No independent redesigns**: product repos consume exports.
- **No claim inheritance**: shared visuals ≠ shared evidence.
- **Provisional**: no trademark assertions, no irreversible renames.

## Consumers

Product repos reference `.github/assets/{brand,github,architecture,screenshots,releases}/`
per the standard. The org profile lives in `profile/`. Docs: read
`USAGE-RULES-v1.0.md` first.