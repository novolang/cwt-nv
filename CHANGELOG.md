# Changelog

All notable changes to cwt-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

## 0.1.0

The first release.

### Added

- **`cwt`**, a token as bytes: `is_tagged` and `kind_of` read the CWT tag and
  the COSE tag, `open` verifies a COSE_Sign1, COSE_Mac0 or COSE_Encrypt0
  CWT, reads its claims and judges them, `open_as` does the same for a token
  whose COSE tag was left off, and `issue_signed`, `issue_maced` and
  `issue_encrypted` make the three kinds, with the CWT tag when asked for.
- **`cwtcheck`**, `CwtRules` and `check`: a list of trusted issuers, the
  audience the recipient answers to, expiration and not-before against a
  clock and a leeway the caller passes, and `require_exp` and `require_nbf`.
- **`cwtcnf`**, the `cnf` claim of RFC 8747: `Cnf` for a COSE_Key, an
  encrypted key and a key identifier, `with_cnf`, `cnf_of`, `key_of` and
  `names_kid`.
- **`cwtclaim`**, the ranges of the CWT claims registry (`key_range`,
  `is_private`), `private_claim`, and `claim_of`, `with_claim` and
  `without_claim` for the claims `CwtClaims` keeps in `extra`.
- **`cwtdev`**, the claims of a token in a `Vec[u8; 512]` with no heap:
  `unwrap` removes the CWT tag, `scan` finds the registered claims and the
  `cnf` claim with its key identifier, `check` judges the times and
  `region_is` compares a text claim with the bytes the device expects.
- **`tests/embedded_probe.nv`**, a firmware program for a door controller,
  built for `--target=nrf52-qemu`. It prints `PASS: cwt-embedded` under QEMU.
  The image is 20,528 bytes of flash and 528 bytes of static RAM.
- Five test suites, among them RFC 8392 appendix A cut out of the RFC's text.

### Not included

- Entity Attestation Tokens (RFC 9711).
- Nested CWTs.
- Decrypting the token of RFC 8392 appendix A.5, which uses AES-CCM-16-64-128;
  cose-nv has no CCM.
- Types for the claims of other registrations, and the proof of possession of
  a `cnf` key.
- Float and tagged times in `cwtdev`.

### Known

- This package overlaps cose-nv's `cosecwt` module, which already holds the
  claims struct, its encoding and the validation of the seven registered
  claims. This package builds on that module and does not replace it.

This release requires novo 0.23.0 or later.
