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

---

## Extension: believed to exist but not retrieved

Investigated 2026-09-25, with the MDL version 1 source rechecked on 2026-11-02. This section lists missing documents, unavailable source variants, and copies recovered elsewhere. Each entry states what is archived and which source remains unavailable.

### RCC 118 / 119

- **Older RCC 118 volumes before 1999/2002.** No copy was found of Volume 1 before 118-06, Volume 2 before 118-02 or Volume 4 after 118-79, and none of 118-XX Volumes 3 or 4 after 1999. The following were checked: the Wayback CDX for `wsmrc2vger.wsmr.army.mil/rcc/`, `wsmr.army.mil/RCCsite/` and `irig106.org/docs/`, the TRMC CQL search (`title~"118"`), and irig106.org `/docs/rcc/118/`.
- **118-02 Volume 2 as PDF.** Only the Word `.doc` from `https://wsmrc2vger.wsmr.army.mil/rcc/manuals/118v2/118-02vol2.doc` (Wayback 20070719) was found. It is archived.
- **118-10 Volume IV (digital recorder) as published.** Only the pink sheet exists. That volume was published as 118-11 Volume V.
- **RCC 119 editions other than 119-06.** None found on irig106.org, TRMC, WSMR RCCsite or wsmrc2vger.
- **Earlier TRMC attachment versions** (the `?version=1` downloads) returned HTTP 404:
  - https://www.trmc.osd.mil/wiki/download/attachments/113019781/118-17v6_Aut_Test_XML_Met.pdf?version=1&api=v2
  - https://www.trmc.osd.mil/wiki/download/attachments/113019799/123-20_IRIG_106_Chapter10_Programmers_Handbook.pdf?version=1&api=v2
- **Truncated or invalid Wayback captures (rejected).** Each of these returned exactly 1,048,576 bytes and failed pdfinfo. A complete copy of each document was archived from another source.
  - https://web.archive.org/web/20210120045435id_/https://www.wsmr.army.mil/RCCsite/Documents/118-20-V1_Test_Methods_Vehicle_TM_Systems/118-20_V1_Vehicle_TM_Systems.pdf
  - https://web.archive.org/web/20210301192311id_/https://www.wsmr.army.mil/RCCsite/Documents/118-20-V5_Test_Digital_Recorder_Reproducers/118-20_Test_Methods_TM_Systems_and_Subsystems_V5.pdf. This is a different file from the TRMC 118-20 V5, but a complete 2020-10 copy was captured at the same URL on 20210822 and is archived.
  - https://web.archive.org/web/20210516052454id_/https://www.wsmr.army.mil/RCCsite/Documents/118-79_Vol_4-Test_Methods_for_Data_Multiplex_Equipment/118-79.pdf
  - https://web.archive.org/web/20190923160114id_/http://www.irig106.org/docs/rcc/118/118-12_Volume_1.pdf, and the same capture date for 118-12_Volume_2, 118-16_…_V5, 118-79_Volume_4 and 118-99_Volume_3.
  - https://web.archive.org/web/20210120044856id_/https://www.wsmr.army.mil/RCCsite/Documents/118-16-Vol-5-Test_Methods_Digital_Recorder_Reproducer_Systems/118-16_Test_Methods_for_TM_Systems_and_Subsystems_V5.pdf returned an HTML page.

### RCC 123 / 124

- **RCC 124-17 TMATS Handbook.** It is still unretrievable, and no new source appeared. URLs tried:
  - https://web.archive.org/web/20210822212902id_/https://www.wsmr.army.mil/RCCsite/Documents/124-17_TMATS_Handbook/124-17_TMATS_Handbook.pdf. This returned HTML. The CDX lists only HTML/301 captures of that URL. The 2018 folder page `Publications.aspx?RootFolder=/RCCsite/Documents/124-17_TMATS_Handbook` confirms the filename, but the PDF itself was never captured.
  - https://www.irig106.org/docs/rcc/124-17_TMATS_Handbook.pdf returned 404, as did https://www.irig106.org/docs/124-17/124-17_TMATS_Handbook.pdf.
  - TRMC CQL `text~"124-17"` returned only 124-22.
  - DTIC (apps.dtic.mil) returned 403.
- **No other missing 123 or 124 editions were found.** Every 123/124 copy found at wsmrc2vger, WSMR RCCsite, irig106.org and TRMC (123-09, 123-16, 123-20, 124-13, 124-15, 124-19, 124-22) is byte-identical to a file already in `manifest.toml`, apart from the truncated captures of 123-16, 123-20, 124-13 and 124-19, which were rejected.

### DDML / IHAL schemas

- **106-15 individual DDML and IHAL XSDs at the original WSMR location** (`.../106-15_Telemetry_Standards/schemas/DDML/*.xsd`, `.../schemas/IHAL/**`). Only HTML error-page captures exist, for example https://web.archive.org/web/20210822212113id_/https://www.wsmr.army.mil/RCCsite/Documents/106-15_Telemetry_Standards/schemas/DDML/Container.xsd. The 106-15 set was archived from TRMC instead, where it is identified by its 106-15 namespaces and version strings.
- **106-15 `schemas/DDML/HTML-DDML.zip`.** Only an HTML capture exists (Wayback 20210822210056). It is probably the same as `DDML_HTML.zip`, which is archived.
- **IHAL for 106-11 and earlier.** None is expected, because IHAL first appeared in 106-13. The DDML 3.0/3.1 schemas are archived for 106-07, 106-09 and 106-11.
- **Separate per-edition DDML/IHAL copies for 106-17 through 106-24R1 do not exist.** Those editions link to the shared "References" location, which holds the 106-15 set.

### Change-marked documents

- **Pink sheets for 106-20, 106-22, 106-23, 106-24 and 106-24R1.** None were found on irig106.org, TRMC (CQL `title~"pink"` and `text~"pink sheet"`) or in the Wayback captures of WSMR "Draft Documents".
- **Chapters 6, 10 and 11 pink sheets for 106-15.** None were found.
- **106-17 pre-release TmNS example XMLs.** 29 of the 30 files in `irig106.org/docs/106_Part_II/Chapter_23_Metadata_Configuration-Appendix_A-Examples_20160304/xml/*.xml` returned Wayback 404 even though the CDX lists them. Example: https://web.archive.org/web/20161231081521id_/http://www.irig106.org:80/docs/106_Part_II/Chapter_23_Metadata_Configuration-Appendix_A-Examples_20160304/xml/AssetAssociations.xml. Only AnalogMeasurementsAndTransducers.xml was retrieved.
- **106-17 pre-release spreadsheets that returned Wayback 404:**
  - https://web.archive.org/web/20161231095738id_/http://www.irig106.org:80/docs/106_Part_II/Chapter_25_Management_Resources-Appendix_A-ManagementResourceMatrix_20160226.xlsx
  - https://web.archive.org/web/20161231095743id_/http://www.irig106.org:80/docs/106_Part_II/Chapter_25_Management_Resources-Appendix_A-ManagementResourceMatrix_20160310.xlsx
  - https://web.archive.org/web/20161231095748id_/http://www.irig106.org:80/docs/106_Part_II/Chapter_27_AppendixB2_RANS.xlsx. The WSMR "Draft Documents" copy of this file was retrieved and is archived.

### TmNS companion files

- **Resolved: TRMC MDL schema version 1.** The [version 1 URL](https://www.trmc.osd.mil/wiki/download/attachments/122454021/23_schema.zip?version=1&api=v2), previously reported as HTTP 404, returned the archived 385,236-byte MDL v1.0.0 bundle on 2026-11-02. Its SHA-256 is `5e1da6ac155fe5bc8c9878637b25ed77f8d711073b19e2cd9f178d30c6cda08e`, matching `23_schema.zip` under 106-17 through 106-24R1. The newer MDL 1.2 bundle is archived separately under 106-23 as `23_schema__trmc.zip`.

- **Truncated Wayback captures of ManagementResourceMatrix.json** (1,048,576 bytes, invalid JSON) were rejected. The complete live irig106.org copy is archived for every edition.
  - https://web.archive.org/web/20210618172040id_/https://www.irig106.org/docs/106-17/ManagementResourceMatrix.json, plus the same file under 106-19 (20190923), 106-20 (20201203) and 106-22 (20220707).
- **The WSMR `references/ManagementResourceMatrix.xlsx`** linked from 106-17 Chapter 25 has only an HTML (login page) capture.
