# Proposed validation input boundary — 2026-11-03

**Proposal only; the CLI contract has not changed.** Coordinator is obtaining
the user's decision before implementing this compatibility change.

## Evidence and assumptions

- Shipped CI reads the fixed repository `manifest.toml`; the documented saved
  inventory example is under `files/audits/`. These usages are verified.
- The existing tests and earlier review note explicitly permit files outside
  the repository. Unknown external consumers may depend on that behavior;
  their usage frequency is unverified. Do not infer absence from this checkout.
- Proposed authority: the resolved repository containing the trusted script,
  with **fixed lexical** input locations: `manifest.toml`, public audit JSON
  below `files/audits/`, and optionally staged candidates under a dedicated
  `files/validation-inputs/` directory. No model-selected root/allowlist option.
- The allowed subdirectories must remain within that trusted repository.
  Resolving a symlinked allowed root into an outside directory must never
  redefine the outside directory as trusted. Reject link/reparse-point roots
  and path components, including links whose targets happen to be inside.
- `parse_manifest(bytes)` remains a parser API. It does not grant filesystem
  access. A trusted operator can stage explicitly approved external input;
  this is not permission for an untrusted model to stage arbitrary files.

## Read-only existing-file evaluation

The current CLI was run against **18 existing public-file cases**, with stdout
and stderr discarded. No corpus documents, credentials or files were modified.
The proposed column is an offline policy model, **not an implemented or tested
security guarantee**. `before exit` distinguishes schema validity from the
fact that all 18 selected files can currently be read.

| Existing case | Before exit | Proposed read |
|---|---:|---|
| Default repository manifest | 0 | allow |
| Relative `manifest.toml` | 0 | allow |
| Absolute in-repository manifest | 0 | allow |
| `./manifest.toml` | 0 | allow |
| `scripts/../manifest.toml` | 0 | deny parent syntax |
| README selected as manifest | 1 | deny location |
| Public audit report selected as manifest | 1 | deny location |
| Absolute parent AGENTS.md selected as manifest | 1 | deny escape |
| Relative saved inventory-before.json | 0 | allow |
| Relative saved inventory-after.json | 0 | allow |
| Absolute in-repository inventory-before.json | 0 | allow |
| Absolute in-repository inventory-after.json | 0 | allow |
| `./files/audits/.../inventory-before.json` | 0 | allow |
| Inventory path containing `../` but resolving inside | 0 | deny parent syntax |
| Existing records.json evidence | 1 | allow; schema still fails |
| Existing summary.json evidence | 1 | allow; schema still fails |
| Existing binding.json evidence | 1 | allow; schema still fails |
| README selected as inventory | 1 | deny location |

Current schema validation passed 11 cases. The modeled policy permits 12
reads and denies six; two otherwise-valid parent-syntax inputs would change
behavior. Known default CI and canonical documented inventory inputs remain
valid. The separately tested valid outside-repository fixture would also be
rejected after a root-confinement change. These are intentional compatibility
costs requiring owner approval, not silently accepted scanner workarounds.

Full local results: ignored
`files/audits/2026-11-03-input-boundary-eval.json`.

## Independent audit-command refactor

The accompanying audit refactor extracts checkpoint loading, streaming
collection, mapping/received-byte checks, record reconciliation, summary
generation and the final exit decision into coherent helpers. It does not
change the validation CLI's input policy. The coordinator independently
verified the offline suite and all 15 old/new comparisons, including replay
of the saved 741 observations: emitted evidence bytes, exit results and
download callback counts match. No network download was involved. Local
comparison evidence is `files/audits/2026-11-03-audit-refactor-equivalence.json`.

One deliberate diagnostic change lies outside those equivalence scenarios:
malformed JSON in `binding.json` now produces a controlled argparse failure
(exit 2), preserving the existing evidence, instead of an uncaught decoder
traceback. A focused regression verifies rejection before any download and
confirms that the corrupt evidence file is not overwritten. The manifest and
inventory binding guard remains mandatory.

## Security regression plan and limits

After approval, test before any file-content read: outside absolute paths,
`..` traversal, mixed Windows separators/drives/UNC paths, sibling directories
sharing a name prefix, a symlinked input file, a symlinked intermediate
directory, and a symlink/junction replacing the entire allowed root. Include
valid relative and absolute in-root files and malformed-but-permitted inputs.
Tests must show rejected files are not read, rather than merely returning a
parse error afterward. Windows reparse-point handling needs actual Windows CI
coverage; no privileges or developer-mode installation should be required.

Normalization alone is insufficient. The resolved candidate must satisfy the
fixed root policy and link/reparse checks. A user-selected `--root` would
move authority back to the untrusted caller and is not this proposal.

A check-then-open implementation is **not race-proof** against an adversary
concurrently replacing directories or links. The proposed argument-injection
boundary assumes trusted script/root ownership and no hostile concurrent
filesystem writer. Stronger deployments need OS sandboxing or descriptor-based
no-follow traversal, with platform-specific support; that larger guarantee is
not implied by a `Path.resolve()` check or ordinary unit tests.

Primary references: [Python pathlib resolution](https://docs.python.org/3.11/library/pathlib.html#pathlib.Path.resolve),
[Python os.open and platform-specific descriptor support](https://docs.python.org/3.11/library/os.html#os.open),
[CodeQL path injection guidance](https://codeql.github.com/codeql-query-help/python/py-path-injection/),
and [OWASP path traversal guidance](https://owasp.org/www-community/attacks/Path_Traversal).
