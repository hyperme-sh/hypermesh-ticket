# hypermesh-ticket

Python library that signs and verifies Hypermesh lease tickets. A ticket is a short HMAC-signed grant (`hm1`, version 1) binding a lease to a tenant, a device, a gateway, and the host WireGuard address the gateway should use. The package name is `hypermesh-ticket`, the import is `hypermesh_ticket`, and this tree is version **0.1.0**. The wire contract is [docs/protocol.md](docs/protocol.md).

## Why

A gateway in front of a leased host has to enforce two facts on every chat request: the lease is the one the renter was granted, and the request goes to that host's WireGuard address. Asking the control plane to re-read the lease on each completion would put the control plane on the chat path. The broker signs the grant while the lease is active. The gateway checks that signature locally and proxies to the peer address inside the ticket until the grant expires or the lease id is revoked.

## How it works

Import `hypermesh_ticket`. HTTP routes live on the [gateway](https://github.com/hyperme-sh/hypermesh-gateway). Lease records live in the control plane. This library turns claims into a token and a token back into claims.

[Spanopticon](https://github.com/hyperme-sh/spanopticon), the Hypermesh broker, builds a `TicketClaims` for an active lease and calls `issue_ticket`. The gateway later calls `verify_ticket` or `honor_ticket` with the same HMAC-SHA256 key. The key is the environment variable `HYPERMESH_TICKET_HMAC_KEY`, held by the control plane. Pass `key=` when the process should not read the environment. If that variable is unset, a built-in development key is used only when `HYPERMESH_DEV` is set or `FASTAPI_ENV=development`.

The token is `hm1.<body>.<signature>`. `body` is the base64url form of canonical JSON (UTF-8, keys sorted, no extra whitespace). `signature` is the base64url form of HMAC-SHA256 over those exact bytes. Base64 padding is removed.

| JSON field | Claim | Meaning |
| --- | --- | --- |
| `v` | | `1` |
| `lid` | `lease_id` | Lease this grant belongs to |
| `did` | `device_id` | Host device |
| `rid` | `gateway_id` | Gateway allowed to honor the ticket |
| `tid` | `tenant_id` | Required when issuing |
| `cid` | `contract_id` | Optional |
| `ca` | `client_address` | WireGuard peer, for example `10.77.0.2/32` |
| `st` | `status` | Issued and accepted only as `active` |
| `pur` | `purpose` | `renter`, `ir`, or `service`. A missing purpose verifies as `renter` |
| `exp` | `exp` | Expiry, Unix seconds |

`service_account`, `service-account`, and `named service account` normalize to `service` before signing.

`verify_ticket` accepts the token when the MAC matches, `v` is 1, the status is `active`, `gateway_id` is the gateway checking the token, the lease id is absent from `revoked_lease_ids`, and `now` is earlier than `exp`. Anything else raises `TicketError` (`bad signature`, `ticket expired`, `ticket revoked`, `ticket is not assigned to this gateway`, and the other reasons in the module). The check is local: it does not call `GET /leases`.

`honor_ticket` is that check for the chat router. On failure it raises `TicketNotReady`, which the gateway maps to HTTP **409** with detail **`instance not ready`**.

`TicketClaims.chat_upstream()` is the host completions URL on the peer address, with the CIDR prefix removed: `http://10.77.0.2:8080/v1/chat/completions` for `10.77.0.2/32`.

Further checks on the verified claims:

- `require_renter_chat_purpose` accepts `renter` and `service`.
- `require_ir_chat_purpose` accepts `ir`.
- `require_ticket_tenant` requires the signed tenant to be the tenant the door resolved.
- `purpose_from_authorization` reads `purpose` from a [controlplane-identity](https://github.com/hyperme-sh/controlplane-identity) API-key exchange JWT (`Authorization: Bearer …`). That decode is local. `issue_ticket` and `verify_ticket` with an explicit key use the standard library.
- `renter_key_fingerprint` is the SHA-256 hex digest of a renter API key (`prefix.secret`), so a door can compare the presented key locally.

A new incompatible ticket needs its own prefix and signed `v`. A token that starts with `hm2` is rejected as malformed.

## Practical use

Python 3.13 or newer. The declared dependency is `controlplane-identity` 0.15.0 from [hyperme-sh/controlplane-identity](https://github.com/hyperme-sh/controlplane-identity) at commit `5aeff3d2c00568f39ca6e8b75c7e63883d3a510b`. That repository is public.

From a checkout, with [uv](https://docs.astral.sh/uv/) 0.11.26:

```sh
git clone https://github.com/hyperme-sh/hypermesh-ticket.git
cd hypermesh-ticket
uv sync --frozen
```

From another project:

```sh
uv add "hypermesh-ticket @ git+https://github.com/hyperme-sh/hypermesh-ticket.git"
```

Sign and verify with an explicit key. These claims are the vector in `tests/hm1-vector.json`, and `issue_ticket` reproduces that token byte for byte.

```python
import uuid
from datetime import UTC, datetime

from hypermesh_ticket import (
    TicketClaims,
    TicketError,
    TicketNotReady,
    honor_ticket,
    issue_ticket,
    require_ir_chat_purpose,
    require_renter_chat_purpose,
    verify_ticket,
)

key = b"fixture-only-hm1-signing-key"
now = datetime(2026, 1, 1, tzinfo=UTC)
claims = TicketClaims(
    lease_id=uuid.UUID(int=101),
    device_id=uuid.UUID(int=102),
    gateway_id=uuid.UUID(int=103),
    client_address="10.77.0.2/32",
    status="active",
    exp=datetime(2030, 1, 1, tzinfo=UTC),
    purpose="renter",
    tenant_id=uuid.UUID(int=104),
    contract_id=uuid.UUID(int=105),
)

token = issue_ticket(claims, key=key)
verified = verify_ticket(token, gateway_id=claims.gateway_id, now=now, key=key)
assert verified == claims
assert verified.chat_upstream() == "http://10.77.0.2:8080/v1/chat/completions"
require_renter_chat_purpose(verified)

try:
    require_ir_chat_purpose(verified)
except TicketNotReady as exc:
    assert exc.status_code == 409
    assert exc.detail == "instance not ready"

try:
    honor_ticket(token, gateway_id=uuid.UUID(int=999), now=now, key=key)
except TicketNotReady as exc:
    assert exc.detail == "instance not ready"

try:
    verify_ticket(
        token,
        gateway_id=claims.gateway_id,
        now=now,
        key=key,
        revoked_lease_ids=[claims.lease_id],
    )
except TicketError as exc:
    assert exc.reason == "ticket revoked"
```

```sh
uv run python example.py
```

To read the key from the environment, export it and omit `key=`:

```sh
export HYPERMESH_TICKET_HMAC_KEY='fixture-only-hm1-signing-key'
```

`HYPERMESH_TICKET_HMAC_KEY` is the signing key. Keep it out of logs, off the event bus, and out of host, renter, and gateway credentials. Set it in any environment that is not a local development configuration.

## How Hypermesh uses it

[Hypermesh](https://hyperme.sh) places an inference lease on a host and a gateway. The control plane assigns the WireGuard peer and the signed lease ticket. [hypermesh-gateway](https://github.com/hyperme-sh/hypermesh-gateway) (`hypermesh-gateway-service` 0.1.0) caches the ticket and applies the peer update. Chat authorization in that service is this library.

Spanopticon calls `issue_ticket` for an active lease. The gateway uses its `hm_gw_` credential when it talks to the control plane to learn assignments. That credential is a gateway API key. The HMAC key that signs the ticket is `HYPERMESH_TICKET_HMAC_KEY`. A renter API key is a third value, compared locally with `renter_key_fingerprint`.

On the chat path the gateway calls `honor_ticket` with its gateway id, the clock, and the lease ids it currently treats as revoked. A valid ticket yields claims, and the gateway proxies the completion to `claims.chat_upstream()`: the host listening on that WireGuard address at port 8080. For peer `10.77.0.2/32` the URL is `http://10.77.0.2:8080/v1/chat/completions`. The ticket carries the peer address. WireGuard key material stays in the host and gateway configuration.

The renter chat door then calls `require_renter_chat_purpose`, which accepts `renter` and `service`. The opt-in IR door calls `require_ir_chat_purpose`, which accepts `ir`. `require_ticket_tenant` checks the signed tenant against the tenant that door resolved. When the caller presents an API-key exchange JWT, `purpose_from_authorization` reads the purpose claim from it.

A failed `honor_ticket` check — bad MAC, wrong gateway, inactive lease, revoked lease id, or expiry — becomes HTTP 409 `instance not ready`. The gateway does that check from the cached ticket. It does not call `GET /leases` for each completion.

## Develop and test

Requires Python 3.13 and uv 0.11.26. The identity dependency is the public git pin above.

```sh
uv sync --frozen
bash scripts/check-package.sh
```

The script checks the lock, runs the suite from source, installs the built wheel in a fresh interpreter, and runs the suite again from a wheel rebuilt from the sdist. Those three runs execute the same tests. `tests/test_protocol.py` covers the `hm1` vector and the rejection rules. The installed-package test signs and verifies in an isolated interpreter and imports only this package.

```sh
bash scripts/check-package.sh --fixtures
```

That form installs the identity wheel described in `tests_artifacts/dependencies/manifest.json`. The sdist omits `tests_artifacts/`. Ordinary CI uses the public git pin.

Public CI is [`.github/workflows/package.yml`](.github/workflows/package.yml) on GitHub-hosted Ubuntu. It runs the same script with ambient git credentials disabled.

Gateway tests live in [hypermesh-gateway](https://github.com/hyperme-sh/hypermesh-gateway). `integration/` is an older launcher from the combined workspace.

## Release and versioning

This tree is package **0.1.0** on release line **0.1**. The wire format stays `hm1` / `v=1` when the package version changes. Tags named `vMAJOR.MINOR.PATCH` are the stable channel. Tags named `test-<commit>` are development snapshots. Qualification artifacts, the published `v0.24.0` record, and the stable-tag publisher are documented in [docs/releasing.md](docs/releasing.md).

## License

Apache License 2.0. See [LICENSE](LICENSE).
