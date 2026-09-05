#!/usr/bin/env python3
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
errors=[]
required=["brand/master/aftergraph-mark.svg","brand/master/aftergraph-wordmark.svg","brand/master/aftergraph-lockup-horizontal.svg","brand/master/aftergraph-lockup-stacked.svg","brand/master/aftergraph-mark-mono.svg","brand/master/aftergraph-mark-inverse.svg","brand/exports/aftergraph-avatar.png","brand/github/aftergraph-github-hero.webp","profile/assets/ecosystem.svg"]
for rel in required:
    p=ROOT/rel
    if not p.exists(): errors.append(f"missing: {rel}")
    elif p.suffix==".svg":
        try: ET.parse(p)
        except Exception as e: errors.append(f"invalid SVG {rel}: {e}")
sp=ROOT/"brand/github/aftergraph-social-preview.png"
if sp.exists():
    with Image.open(sp) as im:
        if im.size!=(1280,640): errors.append(f"social preview wrong size: {im.size}")
    if sp.stat().st_size>=1_000_000: errors.append(f"social preview too large: {sp.stat().st_size}")
if errors:
    print("\n".join(errors)); raise SystemExit(1)
print("OK: Aftergraph organization Visual Asset Standard v1.0 core assets verified.")
