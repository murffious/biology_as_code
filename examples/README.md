# Examples — licence

Everything in `examples/` is covered by the repository's
[samples licence](../LICENSE-SAMPLES.md) (`LicenseRef-BAC-Samples-Attribution`):
free reuse with attribution to this repository and the book. The licence is
declared here at directory level rather than inside each JSON instance, because
the instances validate against schemas with `additionalProperties: false` — an
embedded licence key would make every example fail its own schema.

Embedded reference values keep their own sources and terms (see
`THIRD-PARTY-DATA.json` and the per-file provenance fields); the samples licence
covers the structure and curation, not data this project did not author.
