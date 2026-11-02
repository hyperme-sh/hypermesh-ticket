"""Wire compatibility with tickets issued before the package extraction."""

from datetime import UTC, datetime
import json
from pathlib import Path
import uuid

import pytest
from hypermesh_ticket import (
    TICKET_VERSION,
    TicketClaims,
    TicketError,
    TicketNotReady,
    honor_ticket,
    issue_ticket,
    verify_ticket,
)

VECTOR = json.loads(Path(__file__).with_name("hm1-vector.json").read_text())
KEY = VECTOR["key"].encode()
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def test_previous_broker_ticket_verifies_and_issues_identical_bytes():
    claims = TicketClaims(
        lease_id=uuid.UUID(int=101),
        device_id=uuid.UUID(int=102),
        gateway_id=uuid.UUID(int=103),
        client_address="10.77.0.2/32",
        status="active",
        exp=datetime(2030, 1, 1, tzinfo=UTC),
        tenant_id=uuid.UUID(int=104),
        contract_id=uuid.UUID(int=105),
    )
    assert TICKET_VERSION == 1
    assert issue_ticket(claims, key=KEY) == VECTOR["token"]
    assert (
        verify_ticket(VECTOR["token"], gateway_id=claims.gateway_id, now=NOW, key=KEY)
        == claims
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"gateway_id": uuid.UUID(int=999)},
        {"now": datetime(2030, 1, 1, tzinfo=UTC)},
        {"revoked_lease_ids": [uuid.UUID(int=101)]},
        {"key": b"different-fixture-key"},
    ],
)
def test_existing_wire_ticket_keeps_rejection_rules(kwargs):
    arguments = {"gateway_id": uuid.UUID(int=103), "now": NOW, "key": KEY} | kwargs
    with pytest.raises(TicketError):
        verify_ticket(VECTOR["token"], **arguments)
    with pytest.raises(TicketNotReady):
        honor_ticket(VECTOR["token"], **arguments)


def test_future_wire_prefix_is_rejected():
    token = VECTOR["token"].replace("hm1.", "hm2.", 1)
    with pytest.raises(TicketError, match="malformed"):
        verify_ticket(token, gateway_id=uuid.UUID(int=103), now=NOW, key=KEY)
