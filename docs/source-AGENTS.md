# Hypermesh ticket package context

This family package owns the `hm1` lease ticket protocol and fingerprint helpers.
Its only public module is `hypermesh_ticket`; permitted consumers are declared
in `scripts/import_boundaries.json`. It imports no product implementation.
Preserve ticket bytes, signed tenant/gateway scope, expiry, purpose and revocation
checks. Wire version and package version are separate from the shared library
release train. Read README.md and run this suite plus Hypermesh and gateway tests
when changing the protocol. CI uses the existing self-hosted runner labels.
