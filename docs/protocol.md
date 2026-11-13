# Hypermesh ticket protocol

`hypermesh-ticket` is the Hypermesh library for lease ticket claims,
issuance, local verification, chat-purpose gates and renter-key fingerprints.
Hypermesh and its gateway import the public `hypermesh_ticket` module. It owns
no routes, database tables or service lifecycle.

This tree is package `0.1.0`. That version is independent of the wire format.
The wire format is version 1: `hm1.<body>.<signature>`,
with a canonical JSON body and signed `v=1`. New issuance signs the exact body
with Ed25519 and includes `alg: Ed25519`. The existing `key=` issuance API
retains marker-free HMAC-SHA256 bytes for migration. Verifiers accept legacy
absent/`HS256` markers only before a required timezone-aware overlap deadline
(`hmac_accept_until=` or `HYPERMESH_TICKET_HMAC_ACCEPT_UNTIL`). Unset, malformed,
or elapsed deadlines reject HMAC, including when the key is explicit.

Tenant, device, lease, address, contract, gateway, expiry, purpose and revocation
semantics remain unchanged. Ed25519 verification uses only a public key;
no source signing-key default exists. The README describes verifier-first
migration and configuration. No synchronized peer version is required.

`purpose_from_authorization` uses the declared `controlplane-identity` dependency
to read an authenticated API-key exchange JWT. Applications configure identity
through the existing interface. Ticket issuance and verification with explicit
keys do not load a service; Ed25519 uses cryptography.

An installed wheel imports `hypermesh_ticket` and does not include the
control-plane service (`hypermesh_service`). The gateway depends on this wheel.
Issuance and verification behavior is specified in the README. Release records
are in [releasing.md](releasing.md).

Run `bash scripts/check-package.sh` for standalone fixed-ticket vectors, rejection
cases and installed identity-purpose checks. The retained gateway integration suite
requires its separate consumer workspace. Future incompatible wire formats need a
new signed version and prefix with an explicit compatibility rollout.

The package release contract covers the actual packaged runtime and is compared
with the accepted immutable artifact. Patch versions must preserve it. The signed
wire version remains independent of the package release line.
