# MISSING / not retrieved

These items are believed to exist, or were linked from a source, but no valid copy could be retrieved. Each entry lists the URLs that were tried. Unless noted, the item is simply absent from this archive.

## Documents not retrieved

1. **RCC 124-17, TMATS Handbook.** The WSMR RCC site had a `124-17_TMATS_Handbook/` folder, but the only Wayback capture of the PDF is an HTML page. It is not on TRMC, which lists only 124-22, and not on irig106.org, which has 124-13, 124-15 and 124-19.
   - https://web.archive.org/web/20210822212902id_/https://www.wsmr.army.mil/RCCsite/Documents/124-17_TMATS_Handbook/124-17_TMATS_Handbook.pdf (returned HTML, 179,718 bytes, rejected)
   - https://www.trmc.osd.mil/wiki/rest/api/content/113019802/child/attachment (lists only 124-22)
   - DTIC search fallback: apps.dtic.mil returned 403 / "Under Maintenance" for every request (e.g. https://apps.dtic.mil/sti/pdfs/AD1077368.pdf, https://apps.dtic.mil/sti/trecms/pdf/AD1184404.pdf, https://apps.dtic.mil/sti/pdfs/AD1106301.pdf).
2. **Contents of IRIG 106-96 self-extracting package.** It is an InstallShield self-extracting archive (PE32), not a PDF or zip, so it was not archived: its contents cannot be verified without running it. The 106-96 standard itself is archived twice, once from each source (scanned TRMC copy and irig106.org text PDF).
   - https://www.irig106.org/docs/106-96/IRIG-106-96.exe (1,811,872 bytes)
3. **106-15 TMATS XSD files from the original WSMR location.** Only the HTML-TMATS.zip and change-log.txt captures were valid. The individual XSDs were taken from the TRMC "tmats (schemas)" page instead.
   - Wayback CDX index for `wsmr.army.mil/RCCsite/Documents/` (prefix query) lists only HTML captures for `106-15_Telemetry_Standards/schemas/TMATS` and no individual TMATS `.xsd` captures.

## Pieces never published separately (no URL found anywhere)

- **Single combined PDF of the full standard** for 106-05, 106-07, 106-09, 106-11 and 106-13. Only per-chapter/appendix PDFs were found. ZIP bundles exist for 106-07, 106-13 (Wayback) and 106-15 and are archived as `kind = "full"`.
- **Separate Cover/TOC/Changes/Preface document** for 106-59 through 106-99, 106-00, 106-01 and 106-04. For these editions only the full scanned or combined PDF exists (106-00 and 106-01 also have chapter-group PDFs). 106-05 has only `chapterchanges.pdf`.
- **Individual chapter PDFs** for 106-59 through 106-99 and 106-04. For 106-00, only Chapters 1-5 and Chapter 9 were published separately.
- **TMATS XML schema** for editions before 106-11. 106-07 and 106-09 have an XSD published as `Tmats.xml`, archived as schema.

## Broken links found (valid copy retrieved elsewhere)

- https://www.irig106.org/docs/106-24/chapter10.pdf, chapter11.pdf and chapter12.pdf are 690-byte HTML error pages. The TRMC copies were archived instead.
- TRMC 106-09 page: `appendixA.pdf` and `106-09 Cover - TOC - Changes - Preface.pdf` are Windows `.url` shortcut stubs of 176 and 219 bytes. The irig106.org copies were archived instead.
- TRMC 106-11 page: `appendixA.pdf` and `appendixB.pdf` are `.url` shortcut stubs. The irig106.org copies were archived instead.
- TRMC 106-19 page: the `106-19 Front Matter, Table of Contents.url` shortcut points to https://www.trmc.osd.mil/wiki/download/attachments/83068123/106-19_Cover_TOC_Changes_Preface.pdf, which returns HTML. The front matter was retrieved from the same page's own attachment and from irig106.org.
- Chapter 9 section 9.4.3 links in 106-13, 106-15 and 106-19 point to `www.wsmr.army.mil/RCCsite/...`, a site that no longer resolves. The 106-13 bundle and the 106-15 HTML-TMATS.zip were recovered from the Wayback Machine.
