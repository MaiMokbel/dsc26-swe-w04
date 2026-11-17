ALLOWED = ["https://branch.nour.example", "http://localhost:5173"]
OTHER = ["https://evil.example", "http://localhost:3000",
         "https://branch.nour.example.evil.com"]
ACAO = "access-control-allow-origin"

def preflight(client, origin):
    return client.options("/v1/transfers", headers={
        "Origin": origin, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type"})
def test_preflight_allowed(client):
    for o in ALLOWED:
        r = preflight(client, o)
        assert r.status_code == 200
        assert r.headers[ACAO] == o
        assert r.headers["access-control-allow-credentials"] == "true"
def test_preflight_other_origins_rejected(client):
    for o in OTHER:
        r = preflight(client, o)
        assert r.status_code == 400
        assert ACAO not in r.headers

def test_normal_request_allowed_origin(client):
    for o in ALLOWED:
        r = client.get("/v1/branches/tanta/transfers", headers={"Origin": o})
        assert r.headers[ACAO] == o
        assert r.headers["access-control-allow-credentials"] == "true"
def test_normal_request_other_origin_gets_no_header(client):
    for o in OTHER:
        r = client.get("/v1/branches/tanta/transfers", headers={"Origin": o})
        assert ACAO not in r.headers