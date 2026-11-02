# hypermesh-ticket

Hypermesh family lease-ticket signing and verification. Package version is
**0.1.0**; tickets use the **hm1/v=1** wire format. See [the protocol
contract](docs/protocol.md) for signed scope, purpose, expiry and revocation.

## Development

Requires Python 3.13+, uv 0.11.26 and read access to the private
`hyperme-sh/controlplane-identity` repository over HTTPS.

```sh
uv sync --frozen
bash scripts/check-package.sh
```

Identity is pinned to full commit `13a8257be7762f5e35af63e49136e943a990535c`
in standard distribution metadata and the frozen lock. Ordinary wheel installs
resolve the same dependency without a sibling checkout or workspace override.

Checks exercise fixed signed-ticket vectors, rejection cases and JWT-purpose
integration with the installed identity package. They run from source, a fresh
wheel outside the checkout and a wheel rebuilt from the source archive. Both
wheel payloads are checked against every runtime source file.

The `integration/` suite requires the gateway workspace and is not collected by
the standalone suite. Gateway and Hypermesh consumer integration require their
own checks. `contracts/source-ticket.json` records the API contract snapshot.

## Automated checks

The workflow runs on main pushes and manual dispatches targeting main, using
GitHub-hosted Ubuntu workers and read-only repository permissions. It requires
`DEPENDENCY_READ_TOKEN`, scoped to contents:read on
`hyperme-sh/controlplane-identity` only. The token is supplied only to the check
step through a repository-specific Git HTTPS header; checkout does not retain
credentials. Pull-request branches cannot execute this secret-bearing job.

Actions remains disabled until scoped dependency access and the hosted-worker
policy are configured and a main-commit run succeeds. No dependency credential
is supplied by this repository. The workflow does not publish or deploy.
