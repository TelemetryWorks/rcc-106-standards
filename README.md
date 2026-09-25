# rcc-106-standards

A verified, provenance-preserving mirror of the Range Commanders Council (RCC)
**IRIG Standard 106 Telemetry Standards**, every edition that could be found
from 106-59 through the current **106-24 Revision 1** (January 2025), together
with the companion handbooks **RCC 123** (IRIG 106 Chapter 10 Programmers
Handbook) and **RCC 124** (TMATS Handbook) and the TMATS XML schemas.

It exists so the TelemetryWorks IRIG 106 crates (`irig106-tmats`,
`irig106-time`, `irig106-core`, ...) can cite an exact edition, chapter,
table, and row, and so that citation keeps working when the original sites
move — as the retired `www.wsmr.army.mil/RCCsite` already has.

## What is here

| File | Purpose |
|------|---------|
| `manifest.toml` | One entry per archived file: edition, kind, title, **every original URL** a byte-identical copy was retrieved from, the mirror URL, SHA-256, size, retrieval date, distribution marking, and notes |
| `scripts/fetch.py` | Downloads any subset from the mirror (falling back to the original URLs) and verifies size and SHA-256 |
| `SUMMARY.md` | Per-edition table of what was collected |
| `MISSING.md` | What is known to exist but could not be retrieved, and broken original links |

The documents themselves are **not in the git tree**. Each edition is a
GitHub Release whose tag is the edition name (`106-24R1`, `106-04`,
`rcc-124-22`, ...), and each file is an asset of that release. This keeps
clones small and avoids Git LFS bandwidth quotas.

## Getting documents

Python 3.11 or newer, standard library only:

```bash
python scripts/fetch.py --edition 106-24R1              # one edition
python scripts/fetch.py --chapter 9                     # Chapter 9 of every edition
python scripts/fetch.py --edition 106-23 --chapter 9    # one chapter
python scripts/fetch.py --kind handbook                 # RCC 123 and 124
python scripts/fetch.py                                 # everything (~711 MiB)
python scripts/fetch.py --verify                        # re-check local copies
```

Files land under `files/<edition>/` (ignored by git). Or download a single
asset directly from the edition's release page.

## Provenance

Retrieved 2026-09-25 from:

- `https://www.irig106.org/docs/` (also served as `ftp.irig106.org`),
- the TRMC public RCC wiki (`https://www.trmc.osd.mil/wiki/spaces/publicRCC/`),
- the Internet Archive's captures of the retired `www.wsmr.army.mil/RCCsite`
  for a few items available nowhere else (for example the only full bundle of
  106-13 and the 106-15 TMATS HTML schema bundle).

Every entry records all original URLs, so a document can always be traced
back to where RCC published it.

**Two copies of the same document.** The two sites often host different
issues of the same chapter: TRMC frequently has a later re-issue (for example
106-13 files re-made in 2015, 106-20 in 2022, 106-23 in 2024) while
irig106.org has the original. Both are kept; the irig106.org copy carries the
suffix `__irig106org`, and each entry's `pdf_created` and `note` say which is
which.

## Distribution

RCC publishes these documents publicly, and current editions are marked
**"DISTRIBUTION A: APPROVED FOR PUBLIC RELEASE"**. The manifest's
`distribution` field is `"A"` only where that marking was found in the file
itself (or, for five scanned editions, seen on the rendered cover image).
Chapters of older editions carry the marking only on the edition's cover, and
scanned pre-1986 editions show no marking; those entries say `"unknown"`
rather than assume.

The documents are works of the U.S. Government's Range Commanders Council.
This repository's own files (the manifest, scripts, and documentation) are
licensed under Apache-2.0; that license does not apply to the RCC documents.

## Things to know about the collection

- **Not everything TRMC lists under "106" is a telemetry standard.** 106-59
  is a C-Band radar and beacon standard, 106-64 is "Radio Frequency Sources
  at the National and Service Test Ranges", and the file published as
  `106-62.pdf` is a 1961 "Plan for Global Timing Synchronization". They are
  kept because they are what RCC publishes under those numbers; their
  manifest notes say so.
- **Chapter numbers moved.** From 106-17 the recorder standard was split
  (Chapter 10 recorder operations, Chapter 11 packet formats), and 106-23
  moved randomization into a new Chapter 12. Always check a chapter's title, not only its
  number.
- **The TMATS XML schema bundles are identical across editions.**
  `TmatsXMLSchema.zip` is byte-identical from 106-17 to 106-24R1 and
  `HTML-TMATS.zip` from 106-15 to 106-24R1. They are still attached to each
  edition's release so every edition is complete on its own.
- Gaps and broken original links are listed in `MISSING.md`.

## Adding a new edition

1. Download every document RCC publishes for the edition (full standard,
   front matter, chapters, appendixes, annexes, schemas).
2. Add one `[[document]]` entry per file to `manifest.toml`, with all original
   URLs, SHA-256, size, retrieval date, and distribution marking.
3. Create a release tagged with the edition name and upload each file under
   its manifest `asset` name.
4. Run `python scripts/fetch.py --edition <new> --dest <empty dir>` to prove
   the mirror round trip, then update `SUMMARY.md`.
