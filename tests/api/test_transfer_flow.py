CT = "application/problem+json"

def post(client, item="MET500", frm="heliopolis", to="tanta", qty=5):
    return client.post("/v1/transfers", json={
        "itemCode": item, "fromBranch": frm, "toBranch": to, "quantity": qty})
def units(client, branch, item):
    return client.get(f"/v1/branches/{branch}/stock/{item}").json()["units"]
def assert_problem(resp, status, ptype):
    assert resp.status_code == status
    assert resp.headers["content-type"].split(";")[0] == CT
    body = resp.json()
    assert body["type"] == ptype
    assert body["status"] == status
    assert "title" in body
###creating ###
def test_create_returns_exact_card(client):
    r = post(client)
    assert r.status_code == 201
    assert r.json() == {
        "id": "tr_1", "itemCode": "MET500", "fromBranch": "heliopolis",
        "toBranch": "tanta", "quantity": 5, "priority": "urgent",
        "status": "pending", "requestedAt": "2026-11-03T09:30:00Z"}


def test_ids_increment_in_request_order(client):
    assert post(client).json()["id"] == "tr_1"
    assert post(client).json()["id"] == "tr_2"

def test_priority_uses_destination_stock_and_sales(client):
    # tanta MET500: 2 / 1.0 = 2 days, chronic -> urgent
    assert post(client, "MET500", "heliopolis", "tanta", 1).json()["priority"] == "urgent"
    # tanta AMOX250: 25 / 5 = 5 days, not chronic -> high (not urgent)
    assert post(client, "AMOX250", "heliopolis", "tanta", 1).json()["priority"] == "high"
    # heliopolis has no sales -> normal
    assert post(client, "AMOX250", "tanta", "heliopolis", 1).json()["priority"] == "normal"
def test_request_does_not_move_stock(client):
    post(client, qty=5)
    assert units(client, "heliopolis", "MET500") == 40
    assert units(client, "tanta", "MET500") == 2
def test_extra_body_fields_are_ignored(client):
    r = client.post("/v1/transfers", json={
        "itemCode": "MET500", "fromBranch": "heliopolis", "toBranch": "tanta",
        "quantity": 1, "note": "hi"})
    assert r.status_code == 201
    assert "note" not in r.json()

###request errors
def test_quantity_below_one_is_validation_error(client):
    for q in (0, -3):
        r = post(client, qty=q)
        assert_problem(r, 422, "/problems/validation")
        assert isinstance(r.json()["errors"], list)
def test_missing_field_and_wrong_type_are_validation_errors(client):
    r = client.post("/v1/transfers", json={"itemCode": "MET500", "fromBranch": "heliopolis",
                                           "toBranch": "tanta"})
    assert_problem(r, 422, "/problems/validation")
    r = post(client, qty="lots")
    assert_problem(r, 422, "/problems/validation")

def test_unknown_item_is_404(client):
    assert_problem(post(client, item="NOPE"), 404, "/problems/unknown-item")

def test_unknown_branch_is_404_for_either_side(client):
    assert_problem(post(client, frm="nowhere"), 404, "/problems/unknown-branch")
    assert_problem(post(client, to="nowhere"), 404, "/problems/unknown-branch")
def test_same_branch_is_422(client):
    r = post(client, frm="tanta", to="tanta", qty=1)
    assert_problem(r, 422, "/problems/same-branch")
    assert units(client, "tanta", "MET500") == 2

def test_check_order_item_before_branch_before_same_branch(client):
    assert_problem(post(client, item="NOPE", frm="nowhere", to="nowhere"),
                   404, "/problems/unknown-item")
    assert_problem(post(client, frm="nowhere", to="nowhere"),
                   404, "/problems/unknown-branch")
def test_below_reserve_boundary(client):
    ### heliopolis MET500: 40 units, reserve 10 -> max 30
    assert post(client, qty=30).status_code == 201
    assert_problem(post(client, qty=31), 409, "/problems/below-reserve")
### approving 
def test_approve_moves_stock_exactly_once(client):
    tid = post(client, qty=5).json()["id"]
    r = client.post(f"/v1/transfers/{tid}/approve")
    assert r.status_code == 200
    assert r.json()["status"] == "approved"
    assert units(client, "heliopolis", "MET500") == 35
    assert units(client, "tanta", "MET500") == 7

def test_approve_twice_is_not_pending_and_changes_nothing(client):
    tid = post(client, qty=5).json()["id"]
    client.post(f"/v1/transfers/{tid}/approve")
    assert_problem(client.post(f"/v1/transfers/{tid}/approve"), 409, "/problems/not-pending")
    assert units(client, "heliopolis", "MET500") == 35
    assert units(client, "tanta", "MET500") == 7

def test_approve_unknown_transfer_is_404(client):
    assert_problem(client.post("/v1/transfers/tr_99/approve"), 404, "/problems/unknown-transfer")
def test_approve_refused_when_stock_changed(client):
    a = post(client, qty=20).json()["id"]
    b = post(client, qty=20).json()["id"]  ### both fine at request time
    assert client.post(f"/v1/transfers/{a}/approve").status_code == 200

    assert_problem(client.post(f"/v1/transfers/{b}/approve"), 409, "/problems/below-reserve")
    assert units(client, "heliopolis", "MET500") == 20
    assert units(client, "tanta", "MET500") == 22
    
    assert_problem(client.post(f"/v1/transfers/{b}/approve"), 409, "/problems/below-reserve")
def test_priority_not_recomputed_after_approval(client):
    tid = post(client, qty=5).json()["id"]  ### urgent at request time
    client.post(f"/v1/transfers/{tid}/approve")  ### tanta now has 7 -> would be normal
    items = client.get("/v1/branches/tanta/transfers").json()["items"]
    assert items[0]["priority"] == "urgent"

def test_all_error_kinds_use_problem_media_type(client):
    tid = post(client).json()["id"]
    client.post(f"/v1/transfers/{tid}/approve")
    responses = [
        post(client, qty=0), post(client, item="NOPE"), post(client, to="nowhere"),
        post(client, frm="tanta", to="tanta", qty=1), post(client, qty=999),
        client.post(f"/v1/transfers/{tid}/approve"),
        client.post("/v1/transfers/tr_99/approve"),
    ]
    for r in responses:
        assert r.status_code >= 400
        assert r.headers["content-type"].split(";")[0] == CT