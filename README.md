# cwt-nv

A CBOR Web Token (CWT) is a set of claims about a subject, carried as a
COSE message: a signed, MACed or encrypted CBOR map that says who issued
the token, who it is for, when it is valid, and what key its holder must
prove it holds. It is the token format of constrained devices, specified in
[RFC 8392](https://www.rfc-editor.org/rfc/rfc8392). This package brings it to
novo-lang over [cose-nv](https://novo-lang.org/packages/cose-nv) and
[cbor-nv](https://novo-lang.org/packages/cbor-nv), with the
proof-of-possession claim of
[RFC 8747](https://www.rfc-editor.org/rfc/rfc8747) that
[RFC 9200](https://www.rfc-editor.org/rfc/rfc9200) uses to bind an access
token to a client's key.

## What it is

A door controller is handed a token. It has three questions: is this one of
mine, is it still good, and is it for me. This package answers the first
from the tags, the second and third from the claims, and tells a program
that has a heap and a program that has none how to ask.

**The claims come first.** `CwtClaims` holds the seven registered claims of
RFC 8392 section 3 in fields: the issuer, subject, audience, expiration time,
not-before time, issued-at time and token identifier. Every other pair of the
map is kept in `extra`, with its key, and written back. `cwtclaim` reads and
writes the claims set, with the times as NumericDates (an integer or a float,
with or without tag 1), and holds the claim registry's ranges. Around the
claims the package has:

- the **rules** a recipient judges claims by: a list of trusted issuers, the
  audience it answers to, a clock it passes, and a leeway;
- the **`cnf` claim** of RFC 8747: a key, an encrypted key or a key
  identifier, written and read as a typed value;
- the **kind of a token from its tags**, with or without the CWT tag, and
  one call, `cwt.open`, that dispatches on it, verifies, reads the claims
  and judges them in the order RFC 8392 section 7.2 gives;
- a **reader for a device with no heap** that finds every registered claim
  of a token in a 512-byte buffer.

**The cryptography is cose-nv's.** `cose-nv` carries the COSE messages and the
algorithms (EdDSA, ES256, the HMAC family, AES-GCM, ChaCha20/Poly1305). This
package signs, MACs and encrypts a claims set with them and does not repeat
them.

**The clock is an argument.** Nothing here reads the time. The same token
checks the same way in a test, in a replay and on a device with no
real-time clock.

## Install

```
novo pkg add cwt-nv
```

## Example

A server issues a token for a light, with the confirmation of the client's
key identifier; the light opens it.

```novo
use std.bytes
use cosealg
use cosekey
use cwt
use cwtcheck
use cwtclaim
use cwtcnf

fn issue_and_open() -> Str
    let key = cosekey.symmetric(bytes.from_str("0123456789abcdef0123456789abcdef"))
    let claims = CwtClaims { iss: Some("coap://as.example.com"), sub: Some("erikw"),
                             aud: Some("coap://light.example.com"), exp: Some(1444064944),
                             nbf: Some(1443944944), iat: None, cti: None, extra: [] }
    let bound = cwtcnf.with_cnf(claims, CnfKid(bytes.from_str("client-7")))
    match cwt.issue_maced(CoseHmac256, key, None, bound, bytes.zeros(0), true)
        Err(e)    => e.message()
        Ok(token) =>
            let rules = CwtRules { now: 1444000000, leeway: 5, issuers: ["coap://as.example.com"],
                                   audience: Some("coap://light.example.com"), require_exp: true,
                                   require_nbf: false }
            match cwt.open(token, CoseHmac256, key, bytes.zeros(0), rules)
                Err(e) => e.message()
                Ok(c)  => c.sub ?? "no subject"

fn main() [io]
    println(issue_and_open())   // erikw
```

Build and test with `novo pkg build` and `novo test tests --isolate`.

## What the package contains

| Module | Contents |
| --- | --- |
| `cwtclaim` | `CwtClaims`, the claim keys and the CWT tag, the claims set as a CBOR map or bytes (`claims_to_value`, `claims_to_bytes`, `claims_from_value`, `claims_from_bytes`), the ranges of the registry, private claims, and `claim_of`, `with_claim` and `without_claim` for any claim `CwtClaims` keeps in `extra`. |
| `cwtcheck` | `CwtRules` and `check`: issuer list, audience, expiration and not-before against a clock the caller passes, with a leeway. |
| `cwtcnf` | The `cnf` claim: `Cnf` with its three methods, `with_cnf`, `cnf_of`, `names_kid`. |
| `cwt` | A token as bytes: `is_tagged`, `kind_of`, `open` and `open_as`, which verify and judge it, `issue_signed`, `issue_maced` and `issue_encrypted`, and `sign1`, `mac0` and `encrypt0`, which take the protected and unprotected headers themselves. |
| `cwtdev` | The claims of a token in a `Vec[u8; 512]` with no heap: `unwrap`, `scan`, `check`, `region_is`. |

Every `pub` declaration is documented where it is declared, and
[the package's page](https://novo-lang.org/packages/cwt-nv) is that
reference.

## The rules a user needs

1. **The verifier names the algorithm.** `open` takes the `CoseAlg` the
   recipient uses with the key. A token that names another algorithm is
   refused before any cryptography runs. The token does not choose.
2. **The cryptography comes first.** `open` reads the claims of a token only
   after its signature, tag or AEAD tag has verified, and judges them only
   after that. A claim of a token that did not verify is never read.
3. **The COSE tag names the kind.** A token with tag 18 is a COSE_Sign1, 17 a
   COSE_Mac0 and 16 a COSE_Encrypt0. `open` needs it; a token with the tag
   left off is opened with `open_as` and the kind the caller knows. The CWT
   tag, 61, outside it is accepted and never required, and one tag 61 is
   removed: a second is refused as a COSE tag.
4. **Times are whole seconds the caller read.** A time claim is an integer or a
   float, with or without tag 1; a float is truncated toward zero. A token is
   expired when `now` is at or past `exp + leeway`, and not yet valid when
   `now` is before `nbf - leeway`. The issued-at time is not checked; a recipient that wants
   a maximum age compares it itself.
5. **The checks run in a fixed order:** issuer, audience, expiration,
   not-before. A token that fails two reports the first.
6. **An empty issuer list trusts any issuer.** A list that is not empty
   requires the token to name one of them, and a token with no `iss` fails
   it. An audience that is named requires the token's `aud` to equal it, and
   a token with no `aud` fails.
7. **An expiration time is required by default.** `rules_at` requires one,
   because a token that never expires is a decision for the recipient to
   make, aloud. Set `require_exp` to false to accept it.
8. **A private claim is chosen below -65536.** The registry allocates
   integers from -65536 up and never allocates the range below it, so a
   number there cannot come to mean something else. `private_claim` refuses
   any other.
9. **A confirmation is one method.** `cnf` holds a COSE_Key (1), an
   encrypted key (2) or a key identifier (3), one member only. A map with
   two members, or with a method this package does not know, is refused as
   `cwt: claim 8 is malformed`. That the holder possesses the key is for the
   protocol to show, with a signature or a MAC under it; this package
   carries the claim and does not run that proof.
10. **A device reads definite-length CBOR, integer times and its own
    buffer.** `cwtdev.scan` gives `ok` false for a float time, a time under
    tag 1, an indefinite length, a registered claim of the wrong type, a
    claim twice, or bytes in the region after the map. It reads no more than
    it needs and leaves the rest of the map where it is.

## Running on a microcontroller

`cwtdev` is `@tier(embedded)` and `@no_alloc` throughout. A buffer is a
`Vec[u8; 512]`, the buffer of cose-nv's `cosedev`, which finds the parts of
the COSE message and builds the string a signature or tag covers; a part of a
message is a `Region`, an offset and a length, and nothing is copied. The
four host modules, `cwtclaim`, `cwtcheck`, `cwtcnf` and `cwt`, use `Bytes` and CBOR trees, which are heap
objects, so they are named in `host_modules` and the registry shows the
embedded tier for `cwtdev` alone.

`tests/embedded_probe.nv` is a firmware program for a door controller. It
takes the CWT tag off the MACed token of RFC 8392 appendix A.4, finds the
COSE_Mac0 and its key identifier, reads the claims, judges the times at two
clocks, compares the audience with the string it was provisioned with,
builds the `MAC_structure` that the HMAC is computed over, and reads a
second claims set with a `cnf` claim. It is compiled for a Cortex-M as part
of this package's checks, so the claim is built rather than asserted, and
under QEMU it prints `PASS: cwt-embedded`.

The image is 20,528 bytes of flash and 528 bytes of static RAM, including the
runtime and the board's startup code. The program's own code is 8,206 bytes
of that flash. The probe's frame holds six buffers of 520 bytes and the
claims of two tokens, 160 bytes each.

The HMAC, the signature and the AEAD are the device's own, as in
[cose-nv](https://novo-lang.org/packages/cose-nv): an accelerator, or a
package that builds for the device, with the string `cosedev` builds as
input.

## What is not included

- **Entity Attestation Tokens, RFC 9711.** An EAT is a CWT with more claims
  and a profile; its claims are not here.
- **Nested CWTs.** A token inside a token, with the content type `CWT`, is
  not unwrapped. The payload is read as a claims set.
- **Decrypting RFC 8392 appendix A.5.** The token uses AES-CCM-16-64-128,
  algorithm 10, and cose-nv has no CCM. The token is named as an encrypted
  CWT and its algorithm is refused. `oscore-nv` carries CCM and opens the
  same bytes in its own tests.
- **Claims of other registrations.** Claims beyond the seven and `cnf`, such as
  the ACE-OAuth `scope` or `ace_profile`, are kept as pairs in `extra` and
  read with `claim_of`; nothing here gives them a type.
- **Proof of possession.** The `cnf` claim names a key. Checking that a
  request was made with it is the protocol's.
- **Float and tagged times on a device.** `cwtdev` reads integers.
- **A clock and a random number generator.** The time and the IV are
  arguments.

## Related packages

- [cose-nv](https://novo-lang.org/packages/cose-nv) is the COSE layer this one
  stands on: the messages, the algorithms and the keys.
- [cbor-nv](https://novo-lang.org/packages/cbor-nv) supplies the CBOR value tree
  that the `cnf` claim and the private claims are made of.
- [jwt-nv](https://novo-lang.org/packages/jwt-nv) is the JSON counterpart, for
  tokens that travel as text.

## Tests

The suite is six files under `tests/`.

`tests/cwt_rfc8392_tests.nv` holds the claims set, the keys and the three
tokens of RFC 8392 appendix A. The claims set of A.1 is read and written
again byte for byte. The keys of A.2.1 to A.2.3 are read and rewritten. The
signed token of A.3 is verified against the public key of A.2.3, and a token
signed here under the private key verifies the same way. The MACed token of A.4
is verified and rebuilt byte for byte. The encrypted token of A.5 is named and
refused for its algorithm.
`tests/generate/gen_cwt_vectors.py` cuts the hexadecimal strings out of the
RFC's text into the template next to it, so no byte of them was typed. The key
of A.2.2 is written in the RFC with `alg` 10 where its diagram says HMAC
256/64, and a test records that the key as written is refused for HMAC.

`tests/cwt_edge_tests.nv` holds the claims set beyond the appendix: the
deterministic order of the keys, a time written as an integer, a float or under
tag 1, a registered claim of the wrong type, the boundaries of expiration and
not-before with and without leeway, the issuer and audience checks, and a
token with a valid signature over a payload that is not a claims set.

`tests/cwt_claim_tests.nv` holds the ranges of the registry at their edges,
the confirmation claim as bytes derived by hand from RFC 8747 section 3.1,
and `check` at the edge of every time and with a leeway.

`tests/cwt_open_tests.nv` covers the tags, `open` and `open_as`, and the three
kinds issued and opened, including a token made for another key, and one
whose payload is not a claims set.

`tests/cwtdev_tests.nv` reads claims sets derived byte by byte in its
comments, RFC 8392 A.1, every way a set is unreadable, and the removal of the
CWT tag.

`tests/embedded_probe.nv` is the microcontroller program described above.

## Licence

Apache-2.0. See `LICENSE`.
