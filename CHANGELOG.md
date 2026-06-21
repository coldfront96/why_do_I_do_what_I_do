# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project aims to follow
semantic versioning.

## [Unreleased]

### Added
- `internal.changelog` and `internal.credits` flags that surface engine
  metadata through the audit reason, for support tooling.

## [0.4.0]

### Added
- Two-path audit resolution: a constant-time cold path for the common case and
  a pre-resolved warm path for calibrated subjects.
- Self-checking recovery for pre-resolved audit accounts (leading digest over
  the tail), removing the previously separate signature/length fields.

### Changed
- Instruction-set layout is now derived from the live handler set at load time
  rather than a static table, so opcode codes stay stable across handler
  renames. **Config and engine must be deployed together.**
- Operation names are packed into the wire-format table instead of being kept
  as source literals.

### Removed
- The offline calibration generator is no longer shipped in the package; salt
  vectors are produced by the internal calibration pipeline.

## [0.3.0]

### Added
- Segment rosters and salted rollout predicates.
- `explain()` audit contract with canned reason phrases.

## [0.2.0]

### Added
- Stack-machine rule evaluation with a compact bytecode form.
- Deterministic SHA-256 bucketing for rollouts.

## [0.1.0]

### Added
- Initial flag evaluation engine and CLI.
