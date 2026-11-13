"""Public-only verification and bounded legacy compatibility contracts."""
import ast
import base64
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import secrets
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import hypermesh_ticket as ticket

NOW = datetime(2026, 11, 12, tzinfo=UTC)

@pytest.fixture
def claims():
    return ticket.TicketClaims(uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), '10.77.0.2/32',
        'active', NOW + timedelta(hours=1), tenant_id=uuid.uuid4())

@pytest.fixture
def private():
    return Ed25519PrivateKey.generate()


def test_public_only_verifier_cannot_sign(claims, private, monkeypatch):
    token = ticket.issue_ticket(claims, private_key=private)
    public = private.public_key()
    assert ticket.verify_ticket(token, gateway_id=claims.gateway_id, now=NOW, public_key=public) == claims
    assert ticket.honor_ticket(token, gateway_id=claims.gateway_id, now=NOW, public_key=public) == claims
    with pytest.raises(ticket.TicketError, match='private key required'):
        ticket.issue_ticket(claims, private_key=public)
    forged = ticket.issue_ticket(claims, key=public.public_bytes_raw())
    with pytest.raises(ticket.TicketError):
        ticket.verify_ticket(forged, gateway_id=claims.gateway_id, now=NOW, public_key=public)


@pytest.mark.parametrize('field,value', [('lid', str(uuid.UUID(int=99))), ('tid', str(uuid.UUID(int=99))),
    ('did', str(uuid.UUID(int=99))), ('rid', str(uuid.UUID(int=99))), ('ca', '10.77.0.99'),
    ('pur', 'ir'), ('exp', 9999999999), ('alg', 'HS256'), ('alg', 'unknown'), ('alg', None)])
def test_tampered_claim_or_algorithm_rejected(claims, private, field, value):
    token = ticket.issue_ticket(claims, private_key=private)
    prefix, body, signature = token.split('.')
    payload = json.loads(base64.urlsafe_b64decode(body+'='*(-len(body)%4)))
    payload[field] = value
    changed = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    with pytest.raises(ticket.TicketError):
        ticket.verify_ticket(f'{prefix}.{changed}.{signature}', gateway_id=claims.gateway_id,
            now=NOW, public_key=private.public_key(), key=private.public_key().public_bytes_raw(),
            hmac_accept_until=NOW+timedelta(days=1))


def test_wrong_key_expiry_revocation_and_gateway(claims, private):
    token = ticket.issue_ticket(claims, private_key=private)
    options = dict(gateway_id=claims.gateway_id, now=NOW, public_key=private.public_key())
    for changes in [dict(public_key=Ed25519PrivateKey.generate().public_key()),
                    dict(now=claims.exp), dict(revoked_lease_ids=[claims.lease_id]),
                    dict(gateway_id=uuid.uuid4())]:
        with pytest.raises(ticket.TicketError):
            ticket.verify_ticket(token, **(options | changes))


def test_overlap_accepts_both_then_refuses_hmac(claims, private, monkeypatch):
    monkeypatch.delenv(ticket.TICKET_HMAC_OVERLAP_ENV, raising=False)
    key = secrets.token_bytes(32)
    legacy = ticket.issue_ticket(claims, key=key)
    modern = ticket.issue_ticket(claims, private_key=private)
    options = dict(gateway_id=claims.gateway_id, now=NOW, key=key, public_key=private.public_key())
    for token in [legacy, modern]:
        assert ticket.verify_ticket(token, **options, hmac_accept_until=NOW+timedelta(seconds=1)) == claims
    for end in [None, NOW, NOW-timedelta(seconds=1), NOW.replace(tzinfo=None)]:
        with pytest.raises(ticket.TicketError):
            ticket.verify_ticket(legacy, **options, hmac_accept_until=end)
    assert ticket.verify_ticket(modern, **options) == claims


def test_environment_keys_and_overlap(claims, private, monkeypatch):
    monkeypatch.setenv(ticket.TICKET_PRIVATE_KEY_ENV, base64.b64encode(private.private_bytes_raw()).decode())
    monkeypatch.setenv(ticket.TICKET_PUBLIC_KEY_ENV, base64.b64encode(private.public_key().public_bytes_raw()).decode())
    token = ticket.issue_ticket(claims)
    monkeypatch.delenv(ticket.TICKET_PRIVATE_KEY_ENV)
    assert ticket.verify_ticket(token, gateway_id=claims.gateway_id, now=NOW) == claims
    monkeypatch.setenv(ticket.TICKET_HMAC_ENV, secrets.token_hex(32))
    monkeypatch.setenv(ticket.TICKET_HMAC_OVERLAP_ENV, (NOW+timedelta(hours=2)).isoformat())
    legacy = ticket.issue_ticket(claims, key=ticket.ticket_hmac_key())
    assert ticket.verify_ticket(legacy, gateway_id=claims.gateway_id, now=NOW) == claims
    monkeypatch.setenv(ticket.TICKET_HMAC_OVERLAP_ENV, 'invalid')
    with pytest.raises(ticket.TicketError):
        ticket.verify_ticket(legacy, gateway_id=claims.gateway_id, now=NOW)


@pytest.mark.parametrize('setting', ['HYPERMESH_DEV', 'FASTAPI_ENV'])
def test_development_cannot_supply_a_default_key(claims, monkeypatch, setting):
    for name in [ticket.TICKET_PRIVATE_KEY_ENV, ticket.TICKET_HMAC_ENV]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(setting, 'true' if setting == 'HYPERMESH_DEV' else 'development')
    with pytest.raises(ticket.TicketError):
        ticket.issue_ticket(claims)
    with pytest.raises(ticket.TicketError):
        ticket.ticket_hmac_key()


def test_runtime_has_no_literal_key_defaults():
    for path in Path(ticket.__file__).parent.rglob('*.py'):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for name in node.targets:
                    if isinstance(name, ast.Name) and 'KEY' in name.id and isinstance(node.value, ast.Constant):
                        assert name.id.endswith('_ENV') or name.id == '_MISSING_TICKET_KEY'
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'get':
                if len(node.args)>1 and isinstance(node.args[0], ast.Constant) and 'KEY' in str(node.args[0].value):
                    assert isinstance(node.args[1], ast.Constant) and node.args[1].value in ('', None)
