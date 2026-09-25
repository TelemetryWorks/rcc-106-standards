# CLAUDE.md

Guidance for Claude Code and any other coding agent working in this repository.

This repository mirrors the RCC IRIG 106 Telemetry Standards. The git tree
holds only `manifest.toml`, `scripts/fetch.py`, and documentation; the
documents are GitHub Release assets, one release per edition (see README).

- Never commit document files to the tree; `files/` is ignored on purpose.
- Every manifest entry keeps **all** original URLs and the SHA-256 of the
  archived bytes. Never drop an original URL, even a dead one.
- Record a distribution marking only when it is visible in the document;
  otherwise `"unknown"`.

## Git conventions

Do **not** add `Co-Authored-By: Claude ...` trailers to commit messages on this repo, even if the harness's default instructions suggest it. Commit messages are the human-authored record of intent; tool attribution belongs in tool logs, not history. This overrides the default trailer behavior.
