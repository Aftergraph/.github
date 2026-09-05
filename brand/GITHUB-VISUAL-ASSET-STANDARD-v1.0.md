Ja. For **Aftergraph-org’en** bør vi definere ét canonical **GitHub Visual Asset Standard**, så alle repositories ser ud som dele af samme virksomhed i stedet for 27 projekter der tilfældigvis blev født på samme GitHub-konto. 😅

## Aftergraph GitHub Image Asset Standard v1.0

### 1. Organization-level assets

| AssetCanonical filStørrelseFormatStatus |                                     |                                   |            |             |
| --------------------------------------- | ----------------------------------- | --------------------------------- | ---------- | ----------- |
| **Org Avatar / Brand Mark**             | `aftergraph-avatar.png`             | 1024×1024 master + 500×500 export | PNG        | 🔴 REQUIRED |
| **Org Logo Mark**                       | `aftergraph-mark.svg`               | Vector                            | SVG        | 🔴 REQUIRED |
| **Org Wordmark**                        | `aftergraph-wordmark.svg`           | Vector                            | SVG        | 🔴 REQUIRED |
| **Horizontal Lockup**                   | `aftergraph-lockup-horizontal.svg`  | Vector                            | SVG        | 🔴 REQUIRED |
| **Vertical Lockup**                     | `aftergraph-lockup-stacked.svg`     | Vector                            | SVG        | 🟡 STANDARD |
| **Monochrome Mark**                     | `aftergraph-mark-mono.svg`          | Vector                            | SVG        | 🔴 REQUIRED |
| **Inverse Mark**                        | `aftergraph-mark-inverse.svg`       | Vector                            | SVG        | 🔴 REQUIRED |
| **README Hero**                         | `aftergraph-github-hero.webp`       | 1600×600                          | WebP + PNG | 🔴 REQUIRED |
| **Org Architecture Graphic**            | `aftergraph-ecosystem.svg`          | scalable                          | SVG        | 🔴 REQUIRED |
| **Product Ecosystem Map**               | `aftergraph-product-map.svg`        | scalable                          | SVG        | 🟡 STANDARD |
| **Mission / Philosophy visual**         | `aftergraph-mission.svg`            | scalable                          | SVG        | 🟡 STANDARD |
| **Dark README Hero**                    | `aftergraph-github-hero-dark.webp`  | 1600×600                          | WebP       | 🟡 STANDARD |
| **Light README Hero**                   | `aftergraph-github-hero-light.webp` | 1600×600                          | WebP       | 🟡 STANDARD |

GitHub organization profiles understøtter en offentlig README via `.github/profile/README.md`, og den kan indeholde billeder/GIFs. Organisationen kan også have sin egen profil/avatar. [GitHub Doks](https://docs.github.com/en/organizations/collaborating-with-groups-in-organizations/customizing-your-organizations-profile?utm_source=chatgpt.com)

---

# 2. Hvert eneste repository

Det her skal være vores **mandatory repo visual contract**.

| AssetFilnavnDimensionFormål      |                          |               |                                 |
| -------------------------------- | ------------------------ | ------------- | ------------------------------- |
| 🔴 **Repository Social Preview** | `social-preview.png`     | **1280×640**  | GitHub/social sharing           |
| 🔴 **Repository Hero**           | `hero.webp`              | 1600×600      | README top                      |
| 🔴 **Product/Repo Icon**         | `icon.svg`               | Vector        | Repo identity                   |
| 🔴 **Product Logo**              | `logo.svg`               | Vector        | Canonical product logo          |
| 🔴 **Dark Logo**                 | `logo-dark.svg`          | Vector        | Dark backgrounds                |
| 🔴 **Light Logo**                | `logo-light.svg`         | Vector        | Light backgrounds               |
| 🟡 **Architecture Diagram**      | `architecture.svg`       | Vector        | System overview                 |
| 🟡 **System Context**            | `system-context.svg`     | Vector        | Where repo fits into Aftergraph |
| 🟡 **Primary Screenshot**        | `product-main.webp`      | ≥1440 px wide | Product demonstration           |
| 🟡 **Workflow Graphic**          | `workflow.svg`           | Vector        | Main user/system flow           |
| 🟡 **Component Map**             | `components.svg`         | Vector        | Services/modules                |
| 🟢 **Terminal Demo**             | `terminal-demo.webp/gif` | 1600-ish      | CLI repositories                |
| 🟢 **API Flow**                  | `api-flow.svg`           | Vector        | API/service repos               |
| 🟢 **Data Flow**                 | `data-flow.svg`          | Vector        | Data-intensive repos            |
| 🟢 **Before/After**              | `before-after.webp`      | 1600×900      | UI/product changes              |
| 🟢 **Release Hero**              | `release-vX.Y.webp`      | 1600×900      | Major releases                  |

GitHub selv anbefaler **1280×640 px** til repository social previews. PNG/JPG/GIF accepteres, og filen skal være under **1 MB**. 640×320 er minimumsanbefalingen, men vi standardiserer selvfølgelig på 1280×640, fordi med vilje at vælge den ringere størrelse ville være meget menneskeligt. [GitHub Doks](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview?utm_source=chatgpt.com)

### Social Preview template

Alle repos bør bruge samme struktur:

**Aftergraph symbol → product/repo name → kort descriptor → unik produktfarve/grafisk motif**

Eksempel:

`AFTERGRAPH / WORKS`
**Long-horizon autonomous execution**
`Evidence • Governance • Execution`

Ikke screenshots, 14 badges og mikrotekst presset ind som en PowerPoint fra 2007.

---

# 3. README visual assets

Jeg ville standardisere README'erne til:

| PlaceringAsset        |                        |
| --------------------- | ---------------------- |
| Top                   | `hero.webp`            |
| Under intro           | `product-main.webp`    |
| How it works          | `workflow.svg`         |
| Architecture          | `architecture.svg`     |
| Ecosystem             | `system-context.svg`   |
| Optional capabilities | `components.svg`       |
| Development           | `dev-workflow.svg`     |
| Security              | `trust-boundaries.svg` |
| Release               | `release-process.svg`  |

README-filer er en central GitHub repository surface, og GitHub renderer dem automatisk fra bl.a. repo root eller `.github`. [GitHub Doks](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes?utm_source=chatgpt.com)

---

# 4. Produkt-screenshots

For repositories med faktisk UI, eksempelvis WORKS, RenOS, PULSE osv., bør vi have et standard screenshot-set.

| AssetDimension              |                        |
| --------------------------- | ---------------------- |
| `01-overview.webp`          | 1920×1080              |
| `02-primary-workflow.webp`  | 1920×1080              |
| `03-detail-view.webp`       | 1920×1080              |
| `04-live-state.webp`        | 1920×1080              |
| `05-evidence.webp`          | 1920×1080              |
| `06-mobile.webp`            | 1290×2796 eller native |
| `07-dark-mode.webp`         | 1920×1080              |
| `08-command-interface.webp` | 1920×1080              |

Alle skal være reproducerbare fra produkterne, ikke Photoshop-fantasi forklædt som software. Det bliver vigtigt, når Aftergraph-brandet skal signalere **evidence > claims**.

---

# 5. GitHub App assets

Hvis Aftergraph har GitHub Apps:

| AssetStørrelseStatus |                |          |
| -------------------- | -------------- | -------- |
| App Logo             | **≥200×200**   | REQUIRED |
| Transparent App Mark | 512×512 master | STANDARD |
| Badge-safe version   | 512×512        | STANDARD |
| Dark version         | 512×512        | STANDARD |
| Light version        | 512×512        | STANDARD |

GitHub anbefaler **200×200 px** til GitHub App badges, med PNG/JPG/GIF under 1 MB. Logoet vises inden i en cirkulær badge, så vi skal bygge ekstra safe-area omkring vores mark. [GitHub Doks](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/creating-a-custom-badge-for-your-github-app?utm_source=chatgpt.com)

Det samme princip gælder OAuth App-logoer. [GitHub Doks](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-a-custom-badge-for-your-oauth-app?utm_source=chatgpt.com)

---

# 6. GitHub Marketplace

Hvis eksempelvis en Aftergraph GitHub App senere distribueres via Marketplace, kommer endnu et obligatorisk kit.

| AssetGitHub-spec     |               |
| -------------------- | ------------- |
| **Marketplace Logo** | ≥200×200      |
| **Feature Card**     | **965×482**   |
| Screenshot 01        | ≥1200 px bred |
| Screenshot 02        | ≥1200 px bred |
| Screenshot 03        | ≥1200 px bred |
| Screenshot 04        | ≥1200 px bred |
| Screenshot 05        | ≥1200 px bred |

GitHub tillader op til **5 screenshots** og kræver samme dimension/aspect ratio mellem dem. Feature-card-baggrunden er specifikt **965×482 px**. [GitHub Doks](https://docs.github.com/en/apps/github-marketplace/listing-an-app-on-github-marketplace/writing-a-listing-description-for-your-app?utm_source=chatgpt.com)

---

# 7. Team identities

GitHub Teams kan få egne profilbilleder. Ellers arver de organisationens profilbillede. [GitHub Doks](https://docs.github.com/en/organizations/organizing-members-into-teams/setting-your-teams-profile-picture?utm_source=chatgpt.com)

Så hvis Aftergraph får reelle permanente teams, laver vi:

| EksempelAsset  |                           |
| -------------- | ------------------------- |
| Platform       | `team-platform.png`       |
| Research       | `team-research.png`       |
| Security       | `team-security.png`       |
| Intelligence   | `team-intelligence.png`   |
| Product        | `team-product.png`        |
| Infrastructure | `team-infrastructure.png` |

Standard: **512×512 PNG**, samme geometriske system som Aftergraph-marken, men ikke seks totalt forskellige logoer.

---

# 8. Badges og status visuals

Disse bør **ikke** eksporteres som statiske PNG'er.

Brug dynamiske README badges til:

`build` · `tests` · `coverage` · `release` · `license` · `security` · `docs` · `conformance` · `SBOM` · `provenance`

Men lav en ensartet **badge policy**, så README'en ikke ligner en Formel 1-køredragt.

---

# 9. Architecture visual family

For tekniske Aftergraph-repositories ville jeg desuden gøre disse canonical:

| DiagramFil              |                         |
| ----------------------- | ----------------------- |
| System Context          | `system-context.svg`    |
| Container Architecture  | `architecture.svg`      |
| Component Architecture  | `components.svg`        |
| Execution Flow          | `execution-flow.svg`    |
| Sequence Diagram        | `sequence.svg`          |
| Trust Boundaries        | `trust-boundaries.svg`  |
| Data Flow               | `data-flow.svg`         |
| Deployment Architecture | `deployment.svg`        |
| Agent Architecture      | `agents.svg`            |
| State Machine           | `state-machine.svg`     |
| Evidence Chain          | `evidence-chain.svg`    |
| Repository Dependencies | `repo-dependencies.svg` |

Det her er især relevant for Aftergraph, fordi vores repositories i stigende grad udgør **én samlet architecture graph**, ikke isolerede kodeprojekter.

---

# 10. Canonical repository asset structure

```
.github/
└── assets/
    ├── brand/
    │   ├── logo.svg
    │   ├── logo-dark.svg
    │   ├── logo-light.svg
    │   ├── icon.svg
    │   └── icon.png
    │
    ├── github/
    │   ├── social-preview.png
    │   └── hero.webp
    │
    ├── screenshots/
    │   ├── 01-overview.webp
    │   ├── 02-primary-workflow.webp
    │   ├── 03-detail.webp
    │   └── 04-evidence.webp
    │
    ├── architecture/
    │   ├── system-context.svg
    │   ├── architecture.svg
    │   ├── components.svg
    │   ├── data-flow.svg
    │   ├── execution-flow.svg
    │   ├── trust-boundaries.svg
    │   └── deployment.svg
    │
    ├── demos/
    │   ├── demo.webp
    │   └── terminal-demo.gif
    │
    └── releases/
        └── release-template.svg
```

Og centralt i **Aftergraph** **`.github`**:

```
.github/
├── profile/
│   ├── README.md
│   └── assets/
│       ├── hero.webp
│       ├── ecosystem.svg
│       ├── architecture.svg
│       └── product-map.svg
│
└── brand/
    ├── master/
    │   ├── aftergraph-mark.svg
    │   ├── aftergraph-wordmark.svg
    │   ├── aftergraph-lockup-horizontal.svg
    │   └── aftergraph-lockup-stacked.svg
    │
    ├── exports/
    ├── github/
    ├── marketplace/
    ├── teams/
    └── templates/
```

## Det betyder konkret

For **hver vigtig Aftergraph-repo** vil jeg betragte følgende **7 assets som baseline gate**:

**Logo + icon + README hero + GitHub social preview + primary product visual + architecture diagram + Aftergraph ecosystem/context diagram.**

UI-produkter får screenshot-settet oveni. GitHub Apps får app badge. Marketplace-produkter får Marketplace-pakken.

Så har vi ikke bare "nogle GitHub-billeder". Vi har et **reproducerbart GitHub visual system**, som kan genereres fra én master-brandingpakke og valideres i CI. Det er den del, der gør forskellen mellem branding og en mappe fyldt med PNG'er. 🧬⚡