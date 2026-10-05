"""Install the family and gateway wheels without the Hypermesh service."""

import os
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    "package, code",
    [
        (
            "hypermesh-ticket",
            """
import importlib.util, uuid
from datetime import UTC, datetime, timedelta
from hypermesh_ticket import TicketClaims, issue_ticket, verify_ticket
now = datetime.now(UTC)
claims = TicketClaims(lease_id=uuid.uuid4(), device_id=uuid.uuid4(), gateway_id=uuid.uuid4(), client_address='10.77.0.2/32', status='active', exp=now+timedelta(hours=1), tenant_id=uuid.uuid4())
token = issue_ticket(claims, key=b'isolated-wheel-fixture-key')
assert verify_ticket(token, gateway_id=claims.gateway_id, now=now, key=b'isolated-wheel-fixture-key').lease_id == claims.lease_id
assert importlib.util.find_spec('hypermesh_service') is None
assert importlib.util.find_spec('api') is None
""",
        ),
        (
            "hypermesh-gateway-service",
            """
import importlib.util, sys
from hypermesh_gateway_service.app import create_app
from hypermesh_ticket import honor_ticket
assert create_app()
assert callable(honor_ticket)
assert importlib.util.find_spec('hypermesh_service') is None
assert not any(name.startswith('hypermesh_service') for name in sys.modules)
""",
        ),
    ],
)
def test_installed_package_does_not_require_hypermesh_service(package, code):
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("UV_NO_SYNC", None)
    environment["FASTAPI_ENV"] = "test"
    subprocess.run(
        [
            "uv",
            "run",
            "--isolated",
            "--no-editable",
            "--frozen",
            "--no-dev",
            "--refresh-package",
            package,
            "--package",
            package,
            "python",
            "-c",
            code,
        ],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
