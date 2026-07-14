# Frozen RGCS v2.0.0 Archive

This directory holds the immutable v2.0.0 release artifacts, moved here
unchanged from the top-level `release/` directory (which is reserved for
v3 outputs). SHA256 values in `release/SHA256SUMS.txt` still verify.

**Freeze rule (Agent 01, 2026-07-14): nothing under `archive/v2.0.0/`
may be modified, regenerated, or deleted by any later agent.** The full
frozen source tree is also recoverable from git tag `v2.0.0` and from
`release/rgcs-v2-src-2.0.0.zip` in this directory.

Note: the Linux PyInstaller build tree (`release/linux/`, 919 checksummed
files) was distributed with the v2 release but is not stored in git; its
checksums remain listed in `SHA256SUMS.txt`.
