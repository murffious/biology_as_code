# Security policy

## What counts as a security issue here

This is a zero-dependency Python package that reads its own packaged JSON and
YAML and does no network I/O unless you opt in to the PubMed fetcher. The
surface is small, but it exists. Report privately if you find:

- Code execution or path traversal through a packaged data file, a fixture, a
  contribution JSON, or a pathway pack.
- The opt-in PubMed fetcher sending anything other than the identifiers you gave
  it, or following a redirect it should not.
- A release artefact on PyPI or Zenodo that does not match the tagged source.
- A real person's data anywhere in the repository. The `check_no_human_rows.py`
  gate exists to keep it out; if it missed something, that is a security report,
  not a bug.

A wrong number, a citation that does not say what we claim, or a fabricated
magnitude is **not** a security issue. It is the most serious kind of bug this
project recognises, and it goes through the public
[evidence issue form](https://github.com/murffious/biology_as_code/issues/new?template=evidence.yml)
so the correction is on the record.

## How to report

Use GitHub's private reporting:
**Security → Report a vulnerability** on the repository page, or
<https://github.com/murffious/biology_as_code/security/advisories/new>.

If you cannot use GitHub, email paulmorf@morfengineering.tech with `[security]`
in the subject. Do not open a public issue for anything on the list above.

## What to expect

- Acknowledgement within 7 days.
- A fix or a written decision within 30 days for anything confirmed.
- Credit in the release notes if you want it.

This is a one-maintainer research package. Those windows are honest, not
generous.

## Supported versions

Only the latest release on PyPI receives fixes. There is no long-term support
line; see CONTRIBUTING for when a release branch would be cut.
