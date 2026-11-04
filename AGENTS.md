# Ticket development

Read README.md and docs/protocol.md. Runtime code is in src/hypermesh_ticket.
Preserve hm1/v=1 bytes, signed scope, purpose, expiry and revocation semantics.

Run bash scripts/check-package.sh with existing read access to the pinned private
identity dependency. Source, fresh external-wheel and rebuilt-sdist tests must
pass. Keep full-SHA dependency pins in distribution metadata and uv.lock.
The integration suite also requires the gateway workspace.

Keep Actions disabled until scoped private dependency access and hosted-worker
policy are configured. Use the approved shared-local self-hosted runner group.
