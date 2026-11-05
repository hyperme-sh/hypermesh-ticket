"""Exercise the independently installed identity dependency and ticket scope."""
import importlib.util
from types import SimpleNamespace
import uuid

import pytest
from controlplane_identity import configuration
from controlplane_identity.security.api_key_exchange_jwt import mint_api_key_session_jwt
from hypermesh_ticket import purpose_from_authorization


@pytest.mark.parametrize('purpose', ['renter', 'ir', 'service'])
def test_purpose_uses_installed_identity(purpose, monkeypatch):
    monkeypatch.setattr(configuration, '_configured', SimpleNamespace(
        usable_api_key_exchange_secret=lambda: 'isolated-ticket-test-signing-secret-32-chars'))
    token = mint_api_key_session_jwt(key_record_id=uuid.uuid4(), tenant_id=uuid.uuid4(),
                                     scopes=['chat'], purpose=purpose)
    assert purpose_from_authorization('Bearer ' + token) == purpose
    assert purpose_from_authorization('Bearer invalid-token') is None
    assert importlib.util.find_spec('hypermesh_service') is None
    assert importlib.util.find_spec('api') is None


def test_distribution_metadata_retains_exact_identity_pin():
    from importlib.metadata import requires
    dependencies = requires('hypermesh-ticket')
    identity = [value for value in dependencies if value.startswith('controlplane-identity')]
    assert len(identity) == 1
    assert 'git+https://github.com/hyperme-sh/controlplane-identity.git@797bb4303075e3e7fb54dd42a1451bfe3fd089fa' in identity[0]


@pytest.mark.parametrize('blocked', [False, True])
def test_installed_identity_checks_retirement_when_enforced(monkeypatch, blocked):
    import httpx
    from controlplane_identity import account_lifecycle

    monkeypatch.setattr(configuration, '_configured', SimpleNamespace(
        usable_api_key_exchange_secret=lambda: 'isolated-ticket-test-signing-secret-32-chars'))
    token = mint_api_key_session_jwt(key_record_id=uuid.uuid4(), tenant_id=uuid.uuid4(),
                                     scopes=['chat'], purpose='renter')
    monkeypatch.setenv('ACCOUNT_CLOSURE_ENFORCEMENT_ENABLED', 'true')
    monkeypatch.setenv('ACCOUNT_CLOSURE_GUARD_TOKEN', 'r' * 32)
    monkeypatch.setenv('ACCOUNT_CLOSURE_GUARD_URL', 'https://users.example')
    original = httpx.AsyncClient
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={'blocked': blocked})

    monkeypatch.setattr(account_lifecycle.httpx, 'AsyncClient', lambda **kwargs:
        original(transport=httpx.MockTransport(respond), **kwargs))
    assert purpose_from_authorization('Bearer ' + token) == (None if blocked else 'renter')
    assert requests
