import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

@pytest.mark.anyio
async def test_register_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/api/auth/register", json={"username":"apitest2","email":"apitest2@w.local","password":"test1234"})
        assert r.status_code == 201
        r = await c.post("/api/auth/login", json={"username":"apitest2","password":"test1234"})
        assert r.status_code == 200
        h = {"Authorization": "Bearer " + r.json()["access_token"]}
        r = await c.get("/api/devices", headers=h)
        assert r.status_code == 200
        r = await c.get("/api/devices")
        assert r.status_code == 401
