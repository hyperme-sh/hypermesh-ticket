# Releasing

This tree's package version is **0.1.0** (`pyproject.toml`). `release-policy.json` sets release line **0.1**. The signed wire format is independent of both: `hm1` with payload field `v=1`. See [the protocol](protocol.md).

Compatibility checks against a Spanopticon baseline are described in [release-policy.md](release-policy.md) and in the [Spanopticon release policy](https://github.com/hyperme-sh/spanopticon/blob/main/docs/releases.md). The machine-readable line and version file are `release-policy.json`.

## Qualification on main

[`.github/workflows/package.yml`](../.github/workflows/package.yml) runs `bash scripts/check-package.sh` on pushes to `main`. It keeps the exact wheel and sdist that passed in the Actions artifact `tested-dist` (90-day retention, uncompressed). That workflow does not create a tag or a GitHub release.

`bash scripts/check-package.sh --fixtures` installs the `controlplane-identity` wheel built from the pinned source revision in `tests_artifacts/dependencies/manifest.json`. The manifest records that revision and the wheel digest. The fixture version is the dependency's own version (`0.15.0`), not this package's version. Fixtures stay out of the sdist and the wheel. Pull-request and main CI use the public git pin in `pyproject.toml` directly.

A candidate manifest under `releases/qualification/current/` or `releases/candidate/` is checked against the wheel just built and against the runtime contract exported from that wheel. Gateway deployment and full-system acceptance are separate from this package check.

## Development snapshots

GitHub prereleases named `test-<commit>` are development snapshots. The package version embedded in a snapshot does not reserve a stable version. Records live under `releases/qualification/` with an explicit non-stable classification. Package CI still checks the wheel binding for the current tree alongside any later stable candidate.

## Stable channel

A stable release is a tag `vMAJOR.MINOR.PATCH`. [`.github/workflows/release.yml`](../.github/workflows/release.yml) runs Spanopticon release admission for line `0.1`, using the repository variable `SPANOPTICON_RELEASE_BASELINE_SHA` as the baseline, then the pinned shared publisher. The publisher ships the artifact retained by the main package workflow for that source. It checks the live release, the tag's source revision, and the asset digests. A green caller job is not by itself a release. A `test-<commit>` snapshot cannot be relabeled into the stable channel.

`releases/accepted/` is the record of an immutable stable GitHub release. It currently binds [v0.24.0](https://github.com/hyperme-sh/hypermesh-ticket/releases/tag/v0.24.0) (release id `434687223`, source revision `c4df84d9313fc6a6d6ac5b8204070a8fb42748b0`) to the published wheel and sdist digests in `releases/accepted/provenance.json`. That tag is a published release. The source tree on `main` remains package `0.1.0` on line `0.1`. Install from a checkout of `main` for the version this README describes. Install the assets on the `v0.24.0` release for that tag's bytes.

`SPANOPTICON_RELEASE_BASELINE_SHA` must be the full 40-character commit of a real accepted bundle before admission can succeed. The bundle is `releases/accepted/release.json` plus its contract files and artifact digests. A missing baseline fails closed. Producing the first baseline, qualifying downstream consumers, and deploying a runtime are separate steps from uploading a qualification snapshot.

Patch versions keep the packaged runtime contract. Replacing a published artifact at the same version fails admission. A new ticket wire format needs its own prefix and signed version; it is not a package-version bump.
