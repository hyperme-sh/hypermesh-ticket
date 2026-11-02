# hypermesh-ticket

Private Hypermesh lease-ticket package, extracted with history from Panopticon.
See [the protocol contract](docs/protocol.md) for signed scope, purpose and expiry
semantics. Package version remains **0.1.0** and the wire format remains **hm1/v=1**.
Runtime source and the original fixed-ticket vector are byte-for-byte unchanged.

## Standalone checks

Requires Python 3.13+, uv 0.11.26, and existing SSH read access to the private
`hyperme-sh/controlplane-identity` repository:

```sh
uv sync --frozen
bash scripts/check-package.sh
```

Identity is pinned to full commit `13a8257be7762f5e35af63e49136e943a990535c`
in standard distribution metadata, not only a uv workspace override. The same
pin is therefore used by ordinary wheel installers. This is an extraction-review
commit, not a released tag. All registry dependencies are frozen in `uv.lock`.
The scripts do not obtain, copy or provision credentials.

Checks verify original source bytes, existing signed-ticket vectors/rejections,
and JWT-purpose integration with the independently installed identity package.
They run from source, then outside the checkout against a wheel and a wheel
rebuilt from the sdist. No sibling checkout or monorepo workspace is needed.

## Provenance and remaining integration

`EXTRACTION.json` retains the original history-import receipt for source revision
`2d92d13f38d491c298631b9b9296979c1fbadd19`. `SOURCE-MANIFEST.json` records
relocations and hashes. `contracts/source-ticket.json` preserves the original
public API snapshot. Package and wire versions are unchanged.

The original monorepo wheel suite is retained under `integration/` for provenance;
it also requires the gateway workspace and is not collected by standalone tests.
Its ticket isolation check is covered by the external-wheel suite. Gateway and
Hypermesh integration remain required at paired consumer cutover.

Actions remain disabled. Destination CI needs reviewed private dependency-read
authority, immutable fetch verification and Infra isolation-policy acceptance.
Use the approved least-privilege App/environment pattern at that step; do not
copy Panopticon's deployment credential. No release, consumer/source cutover or
runtime deployment is performed by this packaging PR.
