# Ticket destination guidance

Read README.md and docs/protocol.md. Runtime code is in src/hypermesh_ticket;
contracts/source-ticket.json records the historical API. Preserve hm1/v=1 bytes,
signed scope, purpose, expiry and revocation semantics during extraction.

Run bash scripts/check-package.sh with existing read access to the pinned private
identity dependency. Source and fresh external-wheel tests must pass. The retained
integration/ suite is monorepo-only; gateway/service consumer checks remain a
paired cutover requirement.

Keep dependency full-SHA pins in distributable metadata and uv.lock. Never replace
them with a sibling path, floating branch or undeclared workspace dependency.
Keep Actions disabled until private dependency access and isolated hosted-worker
policy are reviewed. Do not use the monorepo's private self-hosted runner fleet.
