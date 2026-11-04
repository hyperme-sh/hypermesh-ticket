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
    assert 'git+https://github.com/hyperme-sh/controlplane-identity.git@5675e7b617db705a7b0caf25f2d65d8a492f32b1' in identity[0]
