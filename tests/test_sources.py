"""Integration tests for the sources CRUD API endpoints."""

import pytest
from starlette import status

pytestmark = pytest.mark.asyncio

valid_source_payload = {
    "name": "Agro News",
    "url": "https://agronews.example.com",
    "type": "site",
    "enabled": True,
}


async def test_create_source(client):
    response = await client.post("/sources", json=valid_source_payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == valid_source_payload["name"]
    assert "id" in data
    assert "created_at" in data


async def test_get_source(client):
    create_resp = await client.post("/sources", json=valid_source_payload)
    source_id = create_resp.json()["id"]

    response = await client.get(f"/sources/{source_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == source_id


async def test_get_source_not_found(client):
    response = await client.get("/sources/non-existing-source")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_list_sources(client):
    await client.post("/sources", json=valid_source_payload)
    await client.post(
        "/sources",
        json={
            "name": "Another Site",
            "url": "https://another.example.com",
            "type": "site",
        },
    )

    response = await client.get("/sources")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Another Site"


async def test_update_source(client):
    create_resp = await client.post("/sources", json=valid_source_payload)
    source_id = create_resp.json()["id"]

    update_payload = {"enabled": False, "name": "Updated Agro News"}
    response = await client.patch(f"/sources/{source_id}", json=update_payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["enabled"] is False
    assert data["name"] == "Updated Agro News"

    assert data["url"] == valid_source_payload["url"]


async def test_delete_source(client):
    create_resp = await client.post("/sources", json=valid_source_payload)
    source_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/sources/{source_id}")
    assert delete_resp.status_code == status.HTTP_204_NO_CONTENT

    get_resp = await client.get(f"/sources/{source_id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND
