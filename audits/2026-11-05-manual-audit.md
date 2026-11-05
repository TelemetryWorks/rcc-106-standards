# First manual workflow mirror audit — 2026-11-05 UTC

**PASS.** The registered manual workflow ran end to end once on reviewed main
`470638cf66cd3fcd10c017e40556367aea1cfbee`. Every manifest record matched bytes
actually received from GitHub. No document, release asset or provenance changed.

- [Run 41965582867, attempt 1](https://github.com/TelemetryWorks/rcc-106-standards/actions/runs/41965582867):
  `workflow_dispatch`, successful; job ran 04:05:22–04:08:10 UTC.
- Downloads ran 04:05:36–04:07:55 UTC. All 741 returned HTTP 200 on attempt 1;
  zero reused checkpoints, fallback sources or local corpus reads.
- Manifest SHA-256:
  `a48de81efa38ff5641bb55ba0318fb5d5eb1a4923ecba12c1b3b4239c70ea111`.

| Independently reconciled measure | Result |
|---|---:|
| Manifest records / public releases / release assets | 741 / 49 / 741 |
| Received-byte observations / passing records | 741 / 741 |
| Received and hashed bytes, including repeated blobs | 1,021,513,581 |
| Distinct SHA-256 blobs / distinct blob bytes | 643 / 956,042,413 |
| Missing, extra, duplicate assets; size/hash/API digest disagreements | 0 |
| Before/after inventory changes; reused checkpoints | 0 |

## Workflow and artifact proof

Before dispatch, local and live remote main matched the commit above. The exact
registered workflow was inspected using `gh workflow view audit-mirror.yml
--ref 470638cf66cd3fcd10c017e40556367aea1cfbee --yaml`. Dispatch command:
`gh workflow run audit-mirror.yml --ref main`. The returned run's immutable
head SHA and artifact snapshots confirm what actually ran; a moving branch
name alone is not used as execution proof.

The workflow has only a manual trigger, `contents: read`, two inventory and
two streaming download workers, and a 45-minute timeout. All three actions
use the previously reviewed full SHA pins. Checkout does not persist credentials;
`GH_TOKEN` is scoped to the inventory/audit step. Runner logs show only Contents
and Metadata read permissions. No secrets were requested or printed; a log
review found no unmasked GitHub token patterns. Such a pattern check is not a
universal secret detector. Evidence stores public URLs and final hostnames,
not signed redirect query strings.

The `if: always()` retention step completed successfully:

- [Artifact 13387332985](https://github.com/TelemetryWorks/rcc-106-standards/actions/runs/41965582867/artifacts/13387332985),
  name `mirror-audit-41965582867-1`, **270,948 bytes**.
- ZIP SHA-256:
  `98876b69f3ae79e0fec60db7b2ac26dddd16baa3e11bddc90ea34f78a52b9025`.
  This equals both the GitHub artifact API digest and upload-step digest.
- Retention: **30 days**, API expiry **2026-12-05 04:08:05 UTC**. The local ignored
  copy remains available after GitHub expiry if this checkout is retained.

## Independent verification and retained evidence

The verifier used only Python standard-library parsing and GitHub CLI metadata;
it did not import or execute either archived tool snapshot. It checked ZIP CRC
integrity, safe unique members, and exact manifest/tool snapshot bytes against
`git show 470638c:<path>`, plus `commit.txt`. It independently cross-joined all
manifest identities and paths, both inventories, all received-byte checkpoints,
and final record evidence. Every size, SHA-256, GitHub API digest, release/name,
URL, upload state, HTTP status and observation time matched. It recomputed totals
and manifest/inventory bindings rather than trusting the tool's PASS summary.

The coordinator independently opened the raw ZIP without extraction, checked
each member against saved evidence and snapshots against Git, and repeated the
741-row cross-join, totals, zero-reuse and unchanged-inventory checks. The
coordinator also confirmed the live run head, artifact digest and expiry.

Local ignored artifacts:

- `files/audits/manual-41965582867/evidence.zip`: original downloaded artifact.
- Same directory: extracted evidence, `independent-verification.json`, runner
  log and bounded log-review note. No corpus document bodies are included.
- `files/audits/verify_manual_run.py`: independent verification command;
  reproduce with `python files/audits/verify_manual_run.py` while API access is
  available. Existing ZIP bytes are reused, not document downloads.
- [Concise machine evidence](2026-11-05-evidence.json) is tracked; raw artifact,
  logs and verifier are local only. This is not a claim that ignored files are
  distributed through Git or backed up elsewhere.

The successful run establishes this workflow's current end-to-end path. It
does not simulate every cancellation, timeout or GitHub outage. No full corpus
download occurred locally and no archived executable or package was run.
