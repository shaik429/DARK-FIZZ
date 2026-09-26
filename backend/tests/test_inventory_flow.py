"""The problem statement's steel example, end to end through the real API:

receive 100 kg -> move to Production Rack -> deliver 20 -> 3 kg damaged
=> 77 kg on hand, 4 rows in the ledger, and Steel shows as low stock.
"""

from conftest import login


def ids(client, headers):
    locs = {loc["full_name"]: loc["id"] for loc in client.get("/locations", headers=headers).json()}
    steel = client.get("/products?q=STL-001", headers=headers).json()[0]
    return locs, steel["id"]


def run_operation(client, headers, body):
    r = client.post("/operations", json=body, headers=headers)
    assert r.status_code == 201, r.json()
    op = r.json()
    r = client.post(f"/operations/{op['id']}/validate", headers=headers)
    assert r.status_code == 200, r.json()
    assert r.json()["status"] == "done"
    return r.json()


def test_steel_scenario(client, manager):
    locs, steel = ids(client, manager)
    stock, rack = locs["WH/Stock"], locs["WH/Production Rack"]

    run_operation(
        client,
        manager,
        {"type": "receipt", "dest_location_id": stock, "lines": [{"product_id": steel, "quantity": 100}]},
    )
    run_operation(
        client,
        manager,
        {
            "type": "internal",
            "source_location_id": stock,
            "dest_location_id": rack,
            "lines": [{"product_id": steel, "quantity": 100}],
        },
    )
    run_operation(
        client,
        manager,
        {"type": "delivery", "source_location_id": rack, "lines": [{"product_id": steel, "quantity": 20}]},
    )
    run_operation(
        client,
        manager,
        {"type": "adjustment", "dest_location_id": rack, "lines": [{"product_id": steel, "quantity": 77}]},
    )

    product = client.get(f"/products/{steel}", headers=manager).json()
    assert product["on_hand"] == 77
    assert product["stock_status"] == "low"  # reorder minimum is 80

    per_location = client.get(f"/products/{steel}/stock", headers=manager).json()
    assert {s["location"]: s["quantity"] for s in per_location} == {"WH/Stock": 0, "WH/Production Rack": 77}

    moves = client.get(f"/moves?product_id={steel}", headers=manager).json()
    assert len(moves) == 4
    assert [m["quantity"] for m in reversed(moves)] == [100, 100, 20, 3]

    low = {row["sku"]: row for row in client.get("/dashboard/low-stock", headers=manager).json()}
    assert low["STL-001"]["suggested_order_qty"] == 123  # max 200 - 77 on hand


def test_ledger_matches_on_hand(client, manager):
    locs, steel = ids(client, manager)
    run_operation(
        client,
        manager,
        {
            "type": "receipt",
            "dest_location_id": locs["WH/Stock"],
            "lines": [{"product_id": steel, "quantity": 50}],
        },
    )
    run_operation(
        client,
        manager,
        {
            "type": "delivery",
            "source_location_id": locs["WH/Stock"],
            "lines": [{"product_id": steel, "quantity": 15}],
        },
    )
    moves = client.get(f"/moves?product_id={steel}", headers=manager).json()
    stock_id = locs["WH/Stock"]
    in_ = sum(m["quantity"] for m in moves if m["to_location"] == "WH/Stock")
    out = sum(m["quantity"] for m in moves if m["from_location"] == "WH/Stock")
    per_location = client.get(f"/products/{steel}/stock", headers=manager).json()
    assert in_ - out == next(s["quantity"] for s in per_location if s["location_id"] == stock_id) == 35


def test_initial_stock_goes_through_ledger(client, manager):
    locs, _ = ids(client, manager)
    cats = client.get("/categories", headers=manager).json()
    uoms = client.get("/uoms", headers=manager).json()
    r = client.post(
        "/products",
        headers=manager,
        json={
            "sku": "new-001",
            "name": "Hinge",
            "category_id": cats[0]["id"],
            "uom_id": uoms[0]["id"],
            "initial_qty": 40,
            "initial_location_id": locs["WH/Rack A"],
        },
    )
    assert r.status_code == 201, r.json()
    assert r.json()["sku"] == "NEW-001" and r.json()["on_hand"] == 40
    assert len(client.get(f"/moves?product_id={r.json()['id']}", headers=manager).json()) == 1


def test_dashboard_kpis(client, manager):
    locs, steel = ids(client, manager)
    client.post(
        "/operations",
        headers=manager,
        json={
            "type": "receipt",
            "dest_location_id": locs["WH/Stock"],
            "lines": [{"product_id": steel, "quantity": 5}],
        },
    )
    k = client.get("/dashboard/kpis", headers=manager).json()
    assert k["pending_receipts"] == 1 and k["pending_deliveries"] == 0
    assert k["out_of_stock"] == 10


# ------------------------------------------------------------------ errors


def error(r, status, code):
    assert r.status_code == status, r.json()
    assert r.json()["error"] == code, r.json()
    assert r.json()["message"]


def test_over_delivery_is_blocked_and_nothing_changes(client, manager):
    locs, steel = ids(client, manager)
    run_operation(
        client,
        manager,
        {
            "type": "receipt",
            "dest_location_id": locs["WH/Stock"],
            "lines": [{"product_id": steel, "quantity": 10}],
        },
    )
    op = client.post(
        "/operations",
        headers=manager,
        json={
            "type": "delivery",
            "source_location_id": locs["WH/Stock"],
            "lines": [{"product_id": steel, "quantity": 25}],
        },
    ).json()
    error(client.post(f"/operations/{op['id']}/validate", headers=manager), 409, "INSUFFICIENT_STOCK")
    assert client.get(f"/products/{steel}", headers=manager).json()["on_hand"] == 10
    assert client.post(f"/operations/{op['id']}/confirm", headers=manager).json()["status"] == "waiting"


def test_validate_twice_and_cancel_done(client, manager):
    locs, steel = ids(client, manager)
    op = run_operation(
        client,
        manager,
        {
            "type": "receipt",
            "dest_location_id": locs["WH/Stock"],
            "lines": [{"product_id": steel, "quantity": 1}],
        },
    )
    error(client.post(f"/operations/{op['id']}/validate", headers=manager), 409, "INVALID_STATE")
    error(client.post(f"/operations/{op['id']}/cancel", headers=manager), 409, "INVALID_STATE")


def test_bad_operation_input(client, manager):
    locs, steel = ids(client, manager)
    stock = locs["WH/Stock"]
    error(
        client.post(
            "/operations",
            headers=manager,
            json={
                "type": "receipt",
                "dest_location_id": stock,
                "lines": [{"product_id": steel, "quantity": 0}],
            },
        ),
        400,
        "VALIDATION_ERROR",
    )
    error(
        client.post(
            "/operations",
            headers=manager,
            json={
                "type": "internal",
                "source_location_id": stock,
                "dest_location_id": stock,
                "lines": [{"product_id": steel, "quantity": 1}],
            },
        ),
        400,
        "SAME_LOCATION",
    )
    error(
        client.post("/operations", headers=manager, json={"type": "teleport", "lines": []}),
        400,
        "VALIDATION_ERROR",
    )


def test_auth_errors(client):
    error(
        client.post("/auth/login", json={"email": "manager@stocksense.com", "password": "wrong1234"}),
        401,
        "INVALID_CREDENTIALS",
    )
    error(
        client.post("/auth/login", json={"email": "nobody@x.com", "password": "wrong1234"}),
        401,
        "INVALID_CREDENTIALS",
    )
    error(
        client.post(
            "/auth/signup", json={"name": "A", "email": "manager@stocksense.com", "password": "Abcd1234"}
        ),
        409,
        "EMAIL_ALREADY_EXISTS",
    )
    error(
        client.post("/auth/signup", json={"name": "A", "email": "a@b.com", "password": "short"}),
        400,
        "VALIDATION_ERROR",
    )
    error(client.get("/products"), 401, "UNAUTHORIZED")
    error(client.get("/products", headers={"Authorization": "Bearer garbage"}), 401, "UNAUTHORIZED")


def test_signup_then_login_is_staff(client):
    r = client.post("/auth/signup", json={"name": "Ravi", "email": "Ravi@Test.com", "password": "Ravi1234"})
    assert r.status_code == 201 and r.json()["role"] == "staff" and r.json()["email"] == "ravi@test.com"
    login(client, "ravi@test.com", "Ravi1234")


def test_otp_reset_flow(client, monkeypatch):
    sent = {}
    monkeypatch.setattr("app.services.email_service.send_otp", lambda email, otp: sent.update(otp=otp))
    assert client.post("/auth/forgot-password", json={"email": "staff@stocksense.com"}).status_code == 200
    assert client.post("/auth/forgot-password", json={"email": "ghost@x.com"}).status_code == 200  # no leak
    wrong = "000000" if sent["otp"] != "000000" else "111111"
    error(
        client.post(
            "/auth/reset-password",
            json={"email": "staff@stocksense.com", "otp": wrong, "new_password": "NewPass123"},
        ),
        400,
        "INVALID_OTP",
    )
    r = client.post(
        "/auth/reset-password",
        json={"email": "staff@stocksense.com", "otp": sent["otp"], "new_password": "NewPass123"},
    )
    assert r.status_code == 200, r.json()
    login(client, "staff@stocksense.com", "NewPass123")


def test_staff_cannot_manage_products(client, staff):
    error(
        client.post(
            "/products", headers=staff, json={"sku": "X-1", "name": "X", "category_id": 1, "uom_id": 1}
        ),
        403,
        "FORBIDDEN",
    )


def test_product_errors(client, manager):
    error(client.get("/products/99999", headers=manager), 404, "NOT_FOUND")
    error(client.get("/products/abc", headers=manager), 400, "VALIDATION_ERROR")
    error(
        client.post(
            "/products",
            headers=manager,
            json={"sku": "stl-001", "name": "Dup", "category_id": 1, "uom_id": 1},
        ),
        409,
        "DUPLICATE_SKU",
    )
    error(
        client.post(
            "/products", headers=manager, json={"sku": "Z-1", "name": "Z", "category_id": 999, "uom_id": 1}
        ),
        400,
        "INVALID_REFERENCE",
    )
    error(
        client.put(
            "/reorder-rules",
            headers=manager,
            json={"product_id": 1, "warehouse_id": 1, "min_qty": 50, "max_qty": 10},
        ),
        400,
        "VALIDATION_ERROR",
    )
