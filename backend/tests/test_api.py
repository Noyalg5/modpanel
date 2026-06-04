"""
Integration tests for the ModPanel API.
Fixtures (app_client, auth_headers) are defined in conftest.py.
Each test receives a clean database via the app_client fixture.
"""
import pytest


async def test_health_endpoint(app_client):
    resp = await app_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_register_and_login(app_client):
    resp = await app_client.post(
        "/auth/register",
        json={"email": "newuser@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    assert "access_token" in resp.json()

    resp2 = await app_client.post(
        "/auth/login",
        json={"email": "newuser@example.com", "password": "password123"},
    )
    assert resp2.status_code == 200
    assert "access_token" in resp2.json()


async def test_create_project(app_client, auth_headers):
    resp = await app_client.post(
        "/projects",
        json={"name": "Test Project", "description": "Integration test", "location": "London", "status": "draft"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] is not None
    assert data["name"] == "Test Project"


async def test_list_panels(app_client):
    resp = await app_client.get("/panels")
    assert resp.status_code == 200
    assert len(resp.json()) >= 3


async def test_optimiser_run(app_client, auth_headers):
    proj_resp = await app_client.post(
        "/projects",
        json={"name": "Optimiser Integration Test", "status": "active"},
        headers=auth_headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    panel_id = (await app_client.get("/panels")).json()[0]["id"]

    run_resp = await app_client.post(
        "/optimiser/run",
        json={
            "project_id": project_id,
            "panel_type_id": panel_id,
            "wall_width_mm": 6000,
            "wall_height_mm": 2400,
        },
        headers=auth_headers,
    )
    assert run_resp.status_code == 201
    data = run_resp.json()
    assert data["status"] == "complete"
    assert isinstance(data["waste_percentage"], float)
