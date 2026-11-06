# rcc-106-standards

A verified, provenance-preserving mirror of the Range Commanders Council (RCC)
**IRIG Standard 106 Telemetry Standards**, every edition that could be found
from 106-59 through the current **106-24 Revision 1** (January 2025), together
with the companion handbooks **RCC 118** (Test Methods for Telemetry Systems
and Subsystems), **RCC 119** (Telemetry Applications Handbook), **RCC 123**
(IRIG 106 Chapter 10 Programmers Handbook), **RCC 124** (TMATS Handbook),
and **RCC 129** (TmNS Handbook);
the **RCC 200** standard (IRIG Serial Time Code Formats), which Chapter 11
cites for IRIG time;
the TMATS, DDML, and IHAL XML schemas; the Telemetry Network Standard
companion files (Chapters 21–28); and change-marked review drafts ("pink
sheets") that show what changed between editions.

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
python scripts/fetch.py --kind handbook                 # RCC 118, 119, 123, 124, 129
python scripts/fetch.py --edition rcc-129-25            # TmNS handbook and MDL example
python scripts/fetch.py --kind change-marked            # pink sheets and drafts
python scripts/fetch.py --edition rcc-124-17            # TMATS handbook, two source variants
python scripts/fetch.py                                 # everything (~982 MiB)
python scripts/fetch.py --verify                        # re-check local copies
```

Files land under `files/<edition>/` (ignored by git). Or download a single
asset directly from the edition's release page.

## Provenance

Retrieved 2026-09-25, with later additions dated in the manifest, from:

- `https://www.irig106.org/docs/` (also served as `ftp.irig106.org`),
- the TRMC public RCC wiki (`https://www.trmc.osd.mil/wiki/spaces/publicRCC/`),
- the Internet Archive's captures of the retired `www.wsmr.army.mil/RCCsite`
  for a few items available nowhere else (for example the only full bundle of
  106-13 and the 106-15 TMATS HTML schema bundle),
- Spiral Technology's vendor-hosted RCC 124-17 copy and a community-uploaded
  Internet Archive copy labeled DTIC AD1025657, retained as distinct source
  variants of the same January 2017 handbook.

Every entry records its verified source URLs. Some retired publications are
available only from third parties; those records distinguish byte provenance
from official references that corroborate the edition's identity.

**Two copies of the same document.** The two sites often host different
issues of the same chapter: TRMC frequently has a later re-issue (for example
106-13 files re-made in 2015, 106-20 in 2022, 106-23 in 2024) while
irig106.org has the original. Both are kept; the irig106.org copy carries the
suffix `__irig106org`, and each entry's `pdf_created` and `note` say which is
which.

**RCC 124-17 recovery.** The canonical filename denotes the vendor-hosted
copy; `__archive` preserves the distinct Internet Archive bytes under the
same release. Neither source authenticates issuing-organization bytes. Both
PDFs retain a metadata title containing "Draft", despite their visible
January 2017 publication identity and Distribution A covers. Matching extracted
text and three inspected page renders do not prove full visual equivalence
or final-edition authenticity. See the
[archival provenance note](audits/2026-11-06-rcc124-17-archival.md).

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

## Kinds of document

`kind` in the manifest is one of: `full` (a whole edition, or its zip
bundle), `front-matter`, `chapter`, `appendix`, `annex`, `handbook`
(RCC 118/119/123/124/129, release tags like `rcc-118-20`), `standard` (other
RCC standards that IRIG 106 cites: RCC 200, release tag `rcc-200-16`),
`schema` (TMATS,
DDML, IHAL, and MDL XML schemas), `change-marked` (pink sheets and
pre-release drafts; each note says whether it actually carries tracked
changes), and `companion` (cover letters, spreadsheets, and other files
published alongside an edition).

The DDML and IHAL schemas published with 106-15 are the set that Chapter 9 of
106-17 through 106-24R1 links to, so they are stored once, under the 106-15
release. For the Telemetry Network Standard, irig106.org's
`23_schema.zip` is the 2017 MDL v1.0.0 in every edition folder, while TRMC's
copy linked from 106-23 onward is MDL Schema 1.2
(`106-23/tmns/23_schema__trmc.zip`).

The February 2025 RCC 129-25 TmNS Handbook and its system-level MDL example
are stored under `rcc-129-25`. The shared Band Edge Backoff calculator with
C-Band support is stored under `106-24R1/tmns/`, as both the original workbook
and its byte-preserved ZIP distribution. That filing location does not imply
a 2025 publication date for the calculator.

## Standards cited but not mirrored

IRIG 106 depends on standards from other bodies. The TelemetryWorks crates
cite MIL-STD-1553B, ARINC 429, IEEE 1588, IEEE 754, and FIPS PUB 180-4
(the SHA-256 definition behind the TMATS `G\SHA` checksum). These documents
are not copied here; ARINC and IEEE publications are copyrighted.

The following publisher status was checked on **2026-11-02**. Use the edition
and profile required by the particular IRIG 106 edition being implemented.
These status notes preserve historical citations and do not change those
requirements.

| Reference | Publisher status and official source |
|---|---|
| MIL-STD-1553B | DoD ASSIST lists **MIL-STD-1553 Revision C**, dated **2018-02-28**, as active. Retain Revision B where an edition-specific citation requires it. [ASSIST record](https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=36973) |
| ARINC 429 | SAE ITC/AEEC lists **429P1-19**, published **2019-01-22**, as current for **Part 1**. Other parts have their own revisions. [SAE catalog](https://saemobilus.sae.org/standards/arinc429p1-19-429p1-19-digital-information-transfer-system-dits-part-1-functional-description-electrical-interfaces-label-assignments-word-formats) |
| IEEE 1588 | **1588-2019**, published **2020-06-16**, is active and supersedes 1588-2008. Its catalog lists amendments a/b/c/d/e/g (2022-2024) and **1588h-2026** as an approved draft; a final publication date for h was not established. Further amendment projects are listed separately. [IEEE catalog](https://standards.ieee.org/ieee/1588/6825/) |
| IEEE 754 | **754-2019**, published **2019-07-22**, is active. **P754** is a revision project, not a published replacement. [IEEE catalog and project listing](https://standards.ieee.org/ieee/754/6210/) |
| FIPS PUB 180-4 | NIST lists the **August 2015** update as the final publication. Its **2023-03-07** decision to revise the standard is a planned revision, not a final replacement. [NIST publication](https://csrc.nist.gov/pubs/fips/180-4/upd1/final), [revision decision](https://csrc.nist.gov/news/2023/decision-to-revise-fips-180-4) |

## Adding a new edition

Before committing archive metadata, run the [offline validation checks](docs/validation.md).
PR/push CI runs those same checks. A separate manually triggered GitHub Actions
workflow can audit every mirror byte and retain downloadable evidence.

1. Download every document RCC publishes for the edition (full standard,
   front matter, chapters, appendixes, annexes, schemas).
2. Add one `[[document]]` entry per file to `manifest.toml`, with all original
   URLs, SHA-256, size, retrieval date, and distribution marking.
3. Create a release tagged with the edition name and upload each file under
   its manifest `asset` name.
4. Run `python scripts/fetch.py --edition <new> --dest <empty dir>` to prove
   the mirror round trip, then update `SUMMARY.md`.
