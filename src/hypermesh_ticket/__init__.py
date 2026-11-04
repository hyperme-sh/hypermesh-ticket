"""Signed Hypermesh lease ticket.

(s)panopticon (the broker) issues the grant. The Fyber gateway verifies locally
and honors it until exp without GET /leases or any other control-plane HTTP
on the chat path. Not a WireGuard key. Not a JobKind.

Signing key is CP-held: HYPERMESH_TICKET_HMAC_KEY (HMAC-SHA256). Never a
host secret, renter api-key, or hm_gw_ credential. Never put the signing
key on the event bus, in logs, or in site copy.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Collection, Iterable, Literal

TICKET_VERSION = 1
TICKET_PREFIX = "hm1"
TICKET_HMAC_ENV = "HYPERMESH_TICKET_HMAC_KEY"
TICKET_DEV_ENV = "HYPERMESH_DEV"
# In-source fallback is local-compose only. Never used unless HYPERMESH_DEV or FASTAPI_ENV=development.
_DEV_TICKET_HMAC_KEY = "dev-only-hypermesh-ticket-hmac"
INSTANCE_NOT_READY = "instance not ready"
TICKET_STATUS_ACTIVE = "active"
_MISSING_TICKET_KEY = "HYPERMESH_TICKET_HMAC_KEY is required"

# Purpose is a field on the signed ticket, not a Keycloak role and not an IdP.
TICKET_PURPOSE_RENTER = "renter"
TICKET_PURPOSE_IR = "ir"
TICKET_PURPOSE_SERVICE = "service"
TICKET_PURPOSES = frozenset(
    {TICKET_PURPOSE_RENTER, TICKET_PURPOSE_IR, TICKET_PURPOSE_SERVICE}
)
# Renter chat door. IR is the opt-in classified door, not this path.
RENTER_CHAT_PURPOSES = frozenset({TICKET_PURPOSE_RENTER, TICKET_PURPOSE_SERVICE})
IR_CHAT_PURPOSES = frozenset({TICKET_PURPOSE_IR})
# Portal key mint. IR is on the classified door.
KEY_MINT_PURPOSES = frozenset(
    {TICKET_PURPOSE_RENTER, TICKET_PURPOSE_IR, TICKET_PURPOSE_SERVICE}
)
TicketPurpose = Literal["renter", "ir", "service"]
KeyMintPurpose = Literal["renter", "ir", "service"]
_PURPOSE_ALIASES = {
    "named service account": TICKET_PURPOSE_SERVICE,
    "service_account": TICKET_PURPOSE_SERVICE,
    "service-account": TICKET_PURPOSE_SERVICE,
}


class TicketError(Exception):
    """Local verification failed. Router maps this to 409 instance not ready."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class TicketNotReady(Exception):
    """Chat gate: expired, revoked, or otherwise not honor-able."""

    status_code = 409
    detail = INSTANCE_NOT_READY

    def __init__(self) -> None:
        super().__init__(INSTANCE_NOT_READY)


@dataclass(frozen=True)
class TicketClaims:
    lease_id: uuid.UUID
    device_id: uuid.UUID
    gateway_id: uuid.UUID
    client_address: str
    status: str
    exp: datetime
    purpose: str = TICKET_PURPOSE_RENTER
    tenant_id: uuid.UUID | None = None
    contract_id: uuid.UUID | None = None

    def chat_upstream(self) -> str:
        """Standing WG peer target. Chat is http://<client_address>:8080/v1/chat/completions."""

        host = self.client_address.split("/", 1)[0]
        return f"http://{host}:8080/v1/chat/completions"


def normalize_ticket_purpose(raw: object | None) -> str:
    """renter | ir | service. Missing purpose is renter so existing tickets stay live."""

    if raw is None or raw == "":
        return TICKET_PURPOSE_RENTER
    value = str(raw).strip().lower()
    value = _PURPOSE_ALIASES.get(value, value)
    if value not in TICKET_PURPOSES:
        raise TicketError("malformed ticket")
    return value


def require_renter_chat_purpose(claims: TicketClaims) -> TicketClaims:
    """Renter chat door. Accept renter and named service. Reject ir."""

    if claims.purpose not in RENTER_CHAT_PURPOSES:
        raise TicketNotReady()
    return claims


def require_ir_chat_purpose(claims: TicketClaims) -> TicketClaims:
    """Opt-in IR door. Accept ir only. Renter and service stay on default chat."""

    if claims.purpose not in IR_CHAT_PURPOSES:
        raise TicketNotReady()
    return claims


def renter_key_fingerprint(raw: str) -> str:
    """SHA-256 hex of the full prefix.secret. Not bcrypt. Comparable locally."""

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def require_ticket_tenant(claims: TicketClaims, tenant_id: uuid.UUID) -> TicketClaims:
    """Signed tenant must match the tenant the door looked the ticket up under."""

    if claims.tenant_id is None or claims.tenant_id != tenant_id:
        raise TicketNotReady()
    return claims


def purpose_from_authorization(authorization: str) -> str | None:
    """Read purpose from an API-key exchange JWT. Local decode only. Not Keycloak."""

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None
    try:
        from controlplane_identity.security.api_key_exchange_jwt import (
            try_decode_api_key_session_jwt,
        )
    except Exception:
        return None
    claims = try_decode_api_key_session_jwt(token)
    if not claims:
        return None
    raw = claims.get("purpose")
    if raw is None or raw == "":
        return None
    value = str(raw).strip().lower()
    if value not in TICKET_PURPOSES:
        return None
    return value


def _truthy_env(name: str) -> bool:
    return (os.environ.get(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def _dev_ticket_fallback_allowed() -> bool:
    """In-source HMAC key is local-compose only. Do not silently sign prod tickets."""

    if _truthy_env(TICKET_DEV_ENV):
        return True
    return (os.environ.get("FASTAPI_ENV") or "").strip().lower() == "development"


def ticket_hmac_key() -> bytes:
    raw = (os.environ.get(TICKET_HMAC_ENV) or "").strip()
    if raw:
        return raw.encode("utf-8")
    if _dev_ticket_fallback_allowed():
        return _DEV_TICKET_HMAC_KEY.encode("utf-8")
    raise TicketError(_MISSING_TICKET_KEY)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(raw: str) -> bytes:
    pad = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + pad)


def _exp_unix(exp: datetime) -> int:
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=UTC)
    return int(exp.timestamp())


def _claims_payload(claims: TicketClaims) -> dict[str, object]:
    if claims.tenant_id is None:
        raise TicketError("tenant_id is required")
    payload: dict[str, object] = {
        "v": TICKET_VERSION,
        "lid": str(claims.lease_id),
        "did": str(claims.device_id),
        "rid": str(claims.gateway_id),
        "tid": str(claims.tenant_id),
        "ca": claims.client_address,
        "st": claims.status,
        "pur": normalize_ticket_purpose(claims.purpose),
        "exp": _exp_unix(claims.exp),
    }
    if claims.contract_id is not None:
        payload["cid"] = str(claims.contract_id)
    return payload


def _canonical(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _mac(body: bytes, *, key: bytes) -> bytes:
    return hmac.new(key, body, hashlib.sha256).digest()


def issue_ticket(claims: TicketClaims, *, key: bytes | None = None) -> str:
    """Return a compact signed ticket. Caller must only issue for status=active."""

    if claims.status != TICKET_STATUS_ACTIVE:
        raise TicketError("ticket is only issued for an active lease")
    if not claims.client_address.strip():
        raise TicketError("client_address is required")
    normalize_ticket_purpose(claims.purpose)
    signing_key = key if key is not None else ticket_hmac_key()
    body = _canonical(_claims_payload(claims))
    return f"{TICKET_PREFIX}.{_b64url(body)}.{_b64url(_mac(body, key=signing_key))}"


def _parse_token(token: str) -> tuple[dict[str, object], bytes, bytes]:
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != TICKET_PREFIX:
        raise TicketError("malformed ticket")
    try:
        body = _b64url_decode(parts[1])
        sig = _b64url_decode(parts[2])
        payload = json.loads(body.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise TicketError("malformed ticket") from exc
    if not isinstance(payload, dict):
        raise TicketError("malformed ticket")
    return payload, body, sig


def _claims_from_payload(payload: dict[str, object]) -> TicketClaims:
    try:
        exp = datetime.fromtimestamp(int(payload["exp"]), tz=UTC)
        tid_raw = payload.get("tid")
        tenant_id = uuid.UUID(str(tid_raw)) if tid_raw else None
        cid_raw = payload.get("cid")
        contract_id = uuid.UUID(str(cid_raw)) if cid_raw else None
        return TicketClaims(
            lease_id=uuid.UUID(str(payload["lid"])),
            device_id=uuid.UUID(str(payload["did"])),
            gateway_id=uuid.UUID(str(payload["rid"])),
            client_address=str(payload["ca"]),
            status=str(payload["st"]),
            exp=exp,
            purpose=normalize_ticket_purpose(payload.get("pur")),
            tenant_id=tenant_id,
            contract_id=contract_id,
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise TicketError("malformed ticket") from exc


def verify_ticket(
    token: str,
    *,
    gateway_id: uuid.UUID,
    now: datetime | None = None,
    revoked_lease_ids: Collection[uuid.UUID] | Iterable[uuid.UUID] = (),
    key: bytes | None = None,
) -> TicketClaims:
    """Verify signature + exp + assigned gateway locally. Does not call GET /leases."""

    signing_key = key if key is not None else ticket_hmac_key()
    payload, body, sig = _parse_token(token)
    expected = _mac(body, key=signing_key)
    if not hmac.compare_digest(sig, expected):
        raise TicketError("bad signature")
    if int(payload.get("v", 0)) != TICKET_VERSION:
        raise TicketError("unsupported ticket version")
    claims = _claims_from_payload(payload)
    clock = now if now is not None else datetime.now(UTC)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=UTC)
    if claims.status != TICKET_STATUS_ACTIVE:
        raise TicketError("ticket is not active")
    if claims.gateway_id != gateway_id:
        raise TicketError("ticket is not assigned to this gateway")
    if claims.lease_id in set(revoked_lease_ids):
        raise TicketError("ticket revoked")
    if clock >= claims.exp:
        raise TicketError("ticket expired")
    return claims


def honor_ticket(
    token: str,
    *,
    gateway_id: uuid.UUID,
    now: datetime | None = None,
    revoked_lease_ids: Collection[uuid.UUID] | Iterable[uuid.UUID] = (),
    key: bytes | None = None,
) -> TicketClaims:
    """Router chat gate. Valid unexpired ticket → claims. Else 409 instance not ready."""

    try:
        return verify_ticket(
            token,
            gateway_id=gateway_id,
            now=now,
            revoked_lease_ids=revoked_lease_ids,
            key=key,
        )
    except TicketError as exc:
        raise TicketNotReady() from exc


__version__ = "0.1.0"
__all__ = [
    "TICKET_VERSION",
    "TICKET_PREFIX",
    "TICKET_HMAC_ENV",
    "TICKET_DEV_ENV",
    "INSTANCE_NOT_READY",
    "TICKET_STATUS_ACTIVE",
    "TICKET_PURPOSE_RENTER",
    "TICKET_PURPOSE_IR",
    "TICKET_PURPOSE_SERVICE",
    "TICKET_PURPOSES",
    "RENTER_CHAT_PURPOSES",
    "IR_CHAT_PURPOSES",
    "KEY_MINT_PURPOSES",
    "TicketPurpose",
    "KeyMintPurpose",
    "TicketError",
    "TicketNotReady",
    "TicketClaims",
    "normalize_ticket_purpose",
    "require_renter_chat_purpose",
    "require_ir_chat_purpose",
    "renter_key_fingerprint",
    "require_ticket_tenant",
    "purpose_from_authorization",
    "ticket_hmac_key",
    "issue_ticket",
    "verify_ticket",
    "honor_ticket",
]
