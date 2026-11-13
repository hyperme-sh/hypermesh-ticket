"""Transferred ticket isolation assertions from Panopticon's workspace test."""
import os
import subprocess
import sys


def test_installed_package_does_not_require_hypermesh_service(tmp_path):
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("UV_NO_SYNC", None)
    environment["FASTAPI_ENV"] = "test"
    subprocess.run([sys.executable, "-I", "-c", "\nimport importlib.util, uuid\nfrom datetime import UTC, datetime, timedelta\nfrom hypermesh_ticket import TicketClaims, issue_ticket, verify_ticket\nnow = datetime.now(UTC)\nclaims = TicketClaims(lease_id=uuid.uuid4(), device_id=uuid.uuid4(), gateway_id=uuid.uuid4(), client_address='10.77.0.2/32', status='active', exp=now+timedelta(hours=1), tenant_id=uuid.uuid4())\ntoken = issue_ticket(claims, key=b'isolated-wheel-fixture-key')\nassert verify_ticket(token, gateway_id=claims.gateway_id, now=now, key=b'isolated-wheel-fixture-key', hmac_accept_until=now+timedelta(hours=2)).lease_id == claims.lease_id\nassert importlib.util.find_spec('hypermesh_service') is None\nassert importlib.util.find_spec('api') is None\n"], cwd=tmp_path,
                   env=environment, check=True, capture_output=True, text=True)
