import json
import re
from pathlib import Path
from jsonschema.validators import validator_for

SCHEMA = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts" / "transfer_card.schema.json").read_text())
VALIDATOR = validator_for(SCHEMA)(SCHEMA)

KEYS = {"id", "itemCode", "fromBranch", "toBranch", "quantity",
        "priority", "status", "requestedAt"}


def create(client, qty=5):
    return client.post("/v1/transfers", json={
        "itemCode": "MET500", "fromBranch": "heliopolis", "toBranch": "tanta", "quantity": qty})
def test_created_card_matches_schema(client):
    card = create(client).json()
    VALIDATOR.validate(card)
    assert set(card) == KEYS
def test_approved_card_matches_schema(client):
    tid = create(client).json()["id"]
    card = client.post(f"/v1/transfers/{tid}/approve").json()
    VALIDATOR.validate(card)
    assert set(card) == KEYS
def test_inbox_cards_match_schema(client):
    create(client, 1)
    create(client, 2)
    items = client.get("/v1/branches/tanta/transfers").json()["items"]
    assert len(items) == 2
    for card in items:
        VALIDATOR.validate(card)
        assert set(card) == KEYS
def test_requested_at_is_utc_with_z(client):
    card = create(client).json()
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z", card["requestedAt"])
    assert card["requestedAt"] == "2026-11-03T09:30:00Z"