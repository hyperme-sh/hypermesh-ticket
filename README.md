# hypermesh-ticket

## Current version authority

Current development version: `0.1.0`. The services remain before the unreleased
0.24.0 milestone. Earlier 0.24/1.0 preparation and publication notes below are
historical and do not authorize those versions. Existing tags and historical
artifacts remain untouched. Development uses exact source pins and rebuilt
artifacts; no prior release is required. Version changes, tags and publication
require the owner's explicit authorization to the agent.

Hypermesh family lease-ticket signing and verification, licensed under Apache-2.0.
Package version is **0.1.0**; tickets use the **hm1/v=1** wire format.
See [the protocol contract](docs/protocol.md).

## Development

Requires Python 3.13+ and uv 0.11.26. The exact identity dependency is public;
no private credentials or sibling checkout is required.

```sh
uv sync --frozen
bash scripts/check-package.sh
```

The source, externally installed wheel and rebuilt-sdist suites must execute
matching nonempty inventories with no skips. They include the ticket case from
Panopticon's installed-package integration test. Its assertions run in an isolated
interpreter and verify that the plane service is absent. Gateway owns the other
case; the archived monorepo launcher in `integration/` is historical context.

CI uses debrunners while private and hosted Ubuntu when public. Main validation
uses public Git dependencies with ambient Git credentials disabled. Pull requests
also run the real dependency graph. Neither lane needs an App token.

## Release channels

Main validation retains its exact qualified files in Actions artifacts. It does
not create GitHub releases or tags. Historical `test-<commit>` prereleases remain
qualification evidence and do not establish an accepted stable release.

Stable publication requires an explicit `vMAJOR.MINOR.PATCH` tag, the exact
successful main validation artifact, compatible declared contracts and an actual
immutable stable baseline. The publisher independently verifies that evidence;
successful caller jobs alone cannot establish acceptance. Missing evidence and
first-stable bootstrap remain closed. Package qualification, coordinated consumer
acceptance and runtime deployment remain separate.

## Optional fixture qualification

`bash scripts/check-package.sh --fixtures` verifies and installs the identity
wheel built from the exact pinned source revision. The fixture manifest records
its source and digest; the version is the dependency's declared version, not a
release-train number. Fixtures are excluded from distributions. Normal PR and
main CI use public Git dependencies directly, without a private token.
Candidate declarations remain bound to actual wheel bytes and exported runtime
contracts. Gateway deployment and complete-system acceptance are separate.

## Test qualification and stable acceptance

GitHub `test-<commit>` prereleases are development snapshots. Their embedded
package version does not reserve a stable version. Artifact and consumer evidence
lives under `releases/qualification`; the current wheel binding is still checked
by package CI, alongside any future explicit stable candidate. Earlier test
snapshot receipts are preserved there with an explicit non-stable classification.

`releases/accepted` and `SPANOPTICON_RELEASE_BASELINE_SHA` are reserved for an
actual immutable stable GitHub release. The pinned shared guard verifies the live
release channel, stable tag source and asset digests; a test snapshot cannot
become accepted through a provenance label. No stable baseline is recorded until
that release exists. Stable publication remains closed without a valid baseline;
first stable bootstrap and coordinated release qualification remain separate.
No stable version, approval prerequisite or deployment is introduced here.


### Historical stable distribution

The historical accepted record binds the existing immutable `v0.24.0` release to its actual
GitHub release ID, source revision and published asset digests. Test snapshots
remain under `releases/qualification` and do not establish stable acceptance.
Runtime deployment and coordinated consumer acceptance remain separate.

### Actions qualification and stable publication

Main merges and workflow completion do not publish GitHub test releases. Exact
qualification files remain in Actions artifacts with finite retention. The pinned
publisher independently verifies a real immutable stable baseline and refuses
qualification snapshots, even if a caller job reports success. Existing valid
stable records are retained; no release, version change, deployment or human
approval prerequisite is introduced by this correction.
