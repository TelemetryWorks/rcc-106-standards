# Proposed validation input boundary — 2026-11-03

**Owner approved implementation on 2026-11-04; independent source/security
review completed; PR CI and Sonar verification pending.**
The historical proposal/evaluation below is retained. The implementation and
actual replay results are recorded at the end; this document does not claim
that a policy model alone provides security.

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

## Approved implementation and replay — 2026-11-04

The owner approved the fixed-location compatibility change. `load_manifest`
and the CLI inventory read now both use `read_input`, which authorizes the
lexical path against the fixed script-derived repository root before any
content access. The script-derived root retains its lexical checkout identity
rather than resolving away a linked checkout; invocation through a linked
repository entry is rejected. Manifest inputs are the exact repository `manifest.toml` or
staged `.toml` files; inventories are `.json` files in `files/audits/` or
`files/validation-inputs/`. Subdirectories are permitted. There is no CLI root
override and the pure byte parser is unchanged.

The guard rejects parent syntax, drive-relative/network/device paths,
outside absolute paths and sibling-prefix escapes, then checks portable
components and the input-specific location/extension. It walks `lstat` from
the trusted root through every component, rejecting symlinks and all Windows
reparse points before reading, and requires a regular final file. It never
resolves an allowed directory's link target into a new authority. Foreign
Windows drive/backslash syntax is rejected on POSIX; canonical native
separators and mixed Windows separators remain usable on Windows.

Actual read-only replay of the **same 18 existing public-file cases** matches
every proposal decision: **12 allowed, six denied, zero deviations**. All 12
permitted cases retain the prior CLI exit result. Two previously valid
parent-syntax selections now fail before reading; the other four denied
selections previously read an inappropriate file and failed parsing. The
outside-repository fixture regression is intentionally replaced by approved
staging and explicit before-read rejection regressions. Defaults and the
documented saved inventory still pass. No new network download was used.

The 12 preexisting parser/metadata/total/reconciliation helper function ASTs
are exactly unchanged against main `0569fc9`; the intentional differences are
file access and CLI help/dispatch. Local reproducible replay command:
`python files/audits/evaluate_input_boundary.py`. Script and full results are
ignored local artifacts, with results in
`files/audits/2026-11-04-input-boundary-eval.json`; the original baseline is
preserved. These are public-file compatibility observations, not a fresh
mirror byte audit.

New offline regressions assert that blocked paths never invoke the content
read. Coverage includes traversal, outside/sibling paths, Windows drive/UNC/
device/ADS/reserved names, wrong location/extension, valid relative/absolute
and staged inputs, malformed-but-permitted inputs, pure parser independence,
symlink files/directories/allowed roots and actual Windows junctions replacing
intermediate directories, audit/staging/files/repository roots. Local Windows
symlink tests explicitly skip without privilege; real junction tests require
no privilege and execute locally. Ubuntu/Windows CI results remain pending.
The complete local offline suite ran 52 tests successfully (49 executed,
three symlink privilege skips); saved inventory validation retained the
741-record/49-release/643-blob totals and whitespace checks passed.
The coordinator independently repeated these checks and approved the stable
four-file source/security change before publication.

Independent review caught a misplaced junction-test block before publication.
Each native junction scenario now creates and removes its own junction and
asserts the exact reparse rejection diagnostic, with an `lstat` spy proving
the selected link was reached and content was never read. A real copied
module imported and executed through a linked checkout also verifies lexical
root identity, rejection at that root, no content reads, and the actual CLI
diagnostic. These checks prevent outside-root or missing-file failures from
masquerading as junction protection.

Security limits remain as stated above: the trusted root and script must be
owned by the operator, staging needs explicit trusted approval, and hostile
concurrent filesystem mutation requires OS confinement. Hard links do not
establish source provenance; trusted staging/ownership is essential. This
change is neither a race-proof sandbox nor scanner suppression. Actual Sonar
findings must be evaluated after CI; a correct boundary may still require
legitimate issue-specific review if custom validation is not recognized.

Implementation references verified in primary documentation:
[Python lstat and symlink behavior](https://docs.python.org/3.11/library/pathlib.html#pathlib.Path.lstat)
and [Windows reparse attribute constants](https://docs.python.org/3.11/library/stat.html#stat.FILE_ATTRIBUTE_REPARSE_POINT).
