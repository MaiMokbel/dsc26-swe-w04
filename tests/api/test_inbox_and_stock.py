from datetime import UTC, datetime
from fastapi.testclient import TestClient
from nour_transfers.app import create_app
def make_client(now=None):
    app = create_app(
        stock={("heliopolis", "MET500"): 40, ("tanta", "MET500"): 2,
               ("heliopolis", "AMOX250"): 30, ("tanta", "AMOX250"): 25,
               ("heliopolis", "VIT"): 50, ("tanta", "VIT"): 100},
        items={"MET500": {"chronic": True, "reserve": 10},
               "AMOX250": {"chronic": False, "reserve": 5},
               "VIT": {"chronic": False, "reserve": 0}},
        sales={("tanta", "MET500"): 1.0, ("tanta", "AMOX250"): 5.0, ("tanta", "VIT"): 1.0},
        now=now or (lambda: datetime(2026, 11, 3, 9, 30, tzinfo=UTC)),
    )
    return TestClient(app)

def post(c, item, frm, to, qty=1):
    r = c.post("/v1/transfers", json={"itemCode": item, "fromBranch": frm,
                                      "toBranch": to, "quantity": qty})
    assert r.status_code == 201
    return r.json()

def test_inbox_sorted_by_priority_then_request_order():
    c = make_client()
    post(c, "VIT", "heliopolis", "tanta")      ### tr_1 normal
    post(c, "AMOX250", "heliopolis", "tanta")  ### tr_2 high
    post(c, "MET500", "heliopolis", "tanta")   ### tr_3 urgent
    post(c, "AMOX250", "heliopolis", "tanta")  ### tr_4 high
    post(c, "MET500", "heliopolis", "tanta")   ### tr_5 urgent
    items = c.get("/v1/branches/tanta/transfers").json()["items"]
    assert [i["id"] for i in items] == ["tr_3", "tr_5", "tr_2", "tr_4", "tr_1"]
    assert [i["priority"] for i in items] == ["urgent", "urgent", "high", "high", "normal"]


def test_inbox_only_contains_destination_branch_and_keeps_approved():
    c = make_client()
    post(c, "VIT", "heliopolis", "tanta")      ### tr_1
    post(c, "AMOX250", "tanta", "heliopolis")### tr_2, goes to heliopolis
    post(c, "MET500", "heliopolis", "tanta")   ### tr_3
    assert c.post("/v1/transfers/tr_3/approve").status_code == 200
    tanta = c.get("/v1/branches/tanta/transfers").json()["items"]
    assert [i["id"] for i in tanta] == ["tr_3", "tr_1"]
    assert tanta[0]["status"] == "approved"
    hel = c.get("/v1/branches/heliopolis/transfers").json()["items"]
    assert [i["id"] for i in hel] == ["tr_2"]


def test_inbox_empty_for_branch_without_transfers_or_unknown_branch():
    c = make_client()
    assert c.get("/v1/branches/tanta/transfers").json() == {"items": []}
    r = c.get("/v1/branches/nowhere/transfers")
    assert r.status_code == 200
    assert r.json() == {"items": []}


def test_stock_endpoint_shape_and_defaults():
    c = make_client()
    r = c.get("/v1/branches/heliopolis/stock/MET500")
    assert r.status_code == 200
    assert r.json() == {"branch": "heliopolis", "itemCode": "MET500", "units": 40}
    assert c.get("/v1/branches/nowhere/stock/MET500").json()["units"] == 0
    assert c.get("/v1/branches/tanta/stock/NOPE").json()["units"] == 0


def test_each_app_starts_with_no_transfers_and_own_ids():
    a, b = make_client(), make_client()
    assert post(a, "VIT", "heliopolis", "tanta")["id"] == "tr_1"
    assert post(b, "VIT", "heliopolis", "tanta")["id"] == "tr_1"


def test_requested_at_is_clock_at_request_time():
    times = iter([datetime(2026, 11, 3, 9, 30, tzinfo=UTC),
                  datetime(2026, 11, 3, 9, 31, 5, tzinfo=UTC)])
    c = make_client(now=lambda: next(times))
    assert post(c, "VIT", "heliopolis", "tanta")["requestedAt"] == "2026-11-03T09:30:00Z"
    assert post(c, "VIT", "heliopolis", "tanta")["requestedAt"] == "2026-11-03T09:31:05Z"
    approved = c.post("/v1/transfers/tr_1/approve").json()
    assert approved["requestedAt"] == "2026-11-03T09:30:00Z"