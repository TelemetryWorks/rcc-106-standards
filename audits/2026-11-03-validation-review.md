# Validation follow-up and S8707 triage — 2026-11-03

Status: coordinator source review approved; runtime checks passed. SonarCloud
path-issue disposition remains pending. No scanner configuration or issue
status change has been made.

## Findings and exact source/sink paths

SonarCloud's public rule API identifies `pythonsecurity:S8707` as **Agentic
workflows should not be vulnerable to path injection attacks**, created
2026-06-17, with CWE-20/CWE-22 mappings. The public response supplies metadata
but no full rule description. Treating this as exclusively an HTTP/server
rule would miss its stated agentic threat model.

At main commit `2f846e91c85cb9cf66568415d95bbaf894bbe924`, the findings are:

| Issue | Source-to-sink trace |
|---|---|
| `AaGiFwv0XqxoDVw84v8U` (PR #1: `AaGiFkMEXQ1uIZJb9UWL`) | `main(argv)` → `parser.parse_args(argv)` (line 165) → `args.manifest` → `load_manifest(args.manifest)` (line 167) → function argument `path` (line 122) → `pathlib.Path(path).read_bytes()` (line 124). |
| `AaGiFwv0XqxoDVw84v8V` (PR #1: `AaGiFkMEXQ1uIZJb9UWK`) | `main(argv)` → `parser.parse_args(argv)` (line 165) → `args.inventory` → `args.inventory.read_text(encoding="utf-8")` (line 169) → `json.loads` → inventory reconciliation. |

The analyzer describes the arguments as model-supplied and its trace labels
the argument parser as a remote-input source. Actual repository entry points
are local CLIs. Routine CI invokes the default manifest path as a literal
command; the manual workflow likewise uses fixed commands, not model output.
No agent framework, LLM tool registration, service endpoint or model-to-CLI
adapter is shipped in this repository. Coding agents can nevertheless invoke
these CLIs externally, as they did during this work.

## Trust and privilege assessment

`--manifest` and `--inventory` deliberately accept explicitly selected local
files, including absolute paths outside this repository. Reads use the calling
process's OS permissions. There is **no additional input-file capability
confinement** in these options. The metadata `path` validation protects archive
destination names, not the filenames supplied through these two options.

If an agent automatically forwards paths influenced by an untrusted prompt,
document or repository into this CLI while holding broader filesystem
privileges than that task permits, it can read an unintended file. A parent
directory allowlist chosen by that same untrusted agent would not fix this.
Read-only behavior and the existence of other file-reading tools do not by
themselves remove that agentic risk.

The validator parses selected inputs and normally emits derived totals or
diagnostics, not raw file bodies. Invalid TOML is reported without echoing the
input body; inventory mismatch diagnostics can include inventory tag/asset
names. Neither property is an authorization boundary. An agent's ability to
open a file must be limited before parsing if that read is unauthorized.

For a human/operator-selected local-file CLI, arbitrary file selection is an
intentional input capability. For a privileged agent-facing adapter consuming
untrusted model paths, this finding describes a real deployment risk. The
current code and public rule metadata do not justify a blanket false-positive
claim across both deployments.

## Concrete alternatives and proposed disposition

1. Preserve the general local CLI and make no issue-status change until a
   project maintainer reviews the intended caller/trust boundary. This is the
   current follow-up scope; tests retain outside-repository file selection.
2. If an agent-facing deployment is needed, place its process in a filesystem
   sandbox or wrapper whose readable inputs are fixed by a trusted operator,
   with only approved manifest/inventory snapshots mounted. Do not let model
   output expand the allowed roots. This can preserve the CLI while confining
   the agent's effective capability, but requires a separately reviewed
   deployment contract and symlink/absolute/parent-path tests.
3. A CLI-enforced input-root policy would change the existing arbitrary-file
   contract. Do not introduce it merely to satisfy the analyzer. It requires
   explicit design approval and a trusted mechanism for choosing the roots.

Recommended review note: these two findings correctly identify unconstrained
local-file input sinks. The shipped fixed-command CI/local-operator usage is
intentional, while unsandboxed agent forwarding of untrusted paths remains a
deployment risk. A maintainer should choose either a context-specific False
positive disposition for the shipped usage, or Accepted if acknowledging that
agent-facing risk. Neither disposition is authorized by this note. No taint
normalization, `NOSONAR`, rule exclusion, gate change or credentials were added.

## Legitimate issue review workflow

SonarSource documents issue-level **False positive** and **Accept** actions,
both requiring **Administer Issues** permission. A reviewer can use the issue
status menu and attach the trust-boundary explanation. The live public API
metadata also advertises authenticated `POST api/issues/do_transition` with
`issue`, `transition` (`falsepositive` or `accept`) and optional `comment`.
The API requires the same issue-administration permission for those transitions.
GitHub CLI credentials are not SonarCloud authorization and were not reused.
No token was requested, discovered or submitted, and no mutation endpoint was
called. If the permission is unavailable, this remains a maintainer action.

Sources: [live rule metadata](https://sonarcloud.io/api/rules/show?key=pythonsecurity%3AS8707&organization=telemetryworks),
[Sonar issue editing](https://docs.sonarsource.com/sonarqube-cloud/managing-your-projects/issues/editing),
[Sonar project permissions](https://docs.sonarsource.com/sonarqube-cloud/managing-your-projects/administering-your-projects/setting-permissions),
and [live API metadata](https://sonarcloud.io/api/webservices/list?include_internals=false).

## Complexity refactor and validation plan

The separate `python:S3776` finding reports cognitive complexity 75 for
`validate()`. The follow-up extracts coherent text, source-list, number,
metadata, path and cross-record identity validators. Structural failures still
short-circuit semantic checks; semantic failures still participate in
cross-record identity/size checks. Diagnostic ordering and CLI file-selection
behavior are preserved. No scanner policy or path-read sink was changed.

New regressions cover malformed table ordering, structural short-circuiting,
semantic-error identity tracking, explicitly selected files outside the
repository, and avoiding raw invalid-input disclosure. Tests were held during
the spatial maintainer's benchmark window and run after its explicit end.

Validation: all **35 offline tests pass**, saved-inventory reconciliation
passes, and whitespace checks pass. An additional offline comparison loaded
the validator from commit `2f846e9` and compared its exact diagnostic lists
with the refactor across **2,008 cases**, including the complete manifest,
basic malformed tables and 2,000 seeded mutations (seed `8707`). There were
**zero differences**. Machine-readable comparison results are retained locally
in ignored `files/audits/2026-11-03-validation-equivalence.json`.

The manifest SHA-256 remains
`a48de81efa38ff5641bb55ba0318fb5d5eb1a4923ecba12c1b3b4239c70ea111`.
Actual follow-up PR SonarCloud analysis must still establish that S3776 is
resolved; the PR must not merge while remaining security findings are
unresolved. This work performed no additional full mirror audit.
