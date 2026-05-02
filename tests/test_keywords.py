import pytest
from starlette import status

pytestmark = pytest.mark.asyncio

valid_keyword_payload = {
    "word": "wheat",
    "enabled": True,
}


async def test_create_keyword(client):
    response = await client.post("/keywords", json=valid_keyword_payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["word"] == valid_keyword_payload["word"]
    assert "id" in data
    assert "created_at" in data


async def test_get_keyword(client):
    create_resp = await client.post("/keywords", json=valid_keyword_payload)
    keyword_id = create_resp.json()["id"]

    response = await client.get(f"/keywords/{keyword_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == keyword_id


async def test_get_keyword_not_found(client):
    response = await client.get("/keywords/non-existing-source")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_list_keywords(client):
    await client.post("/keywords", json=valid_keyword_payload)
    await client.post(
        "/keywords",
        json={
            "word": "another-keyword",
        },
    )

    response = await client.get("/keywords")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    words = {item["word"] for item in data}
    assert words == {"wheat", "another-keyword"}


async def test_update_keyword(client):
    create_resp = await client.post("/keywords", json=valid_keyword_payload)
    keyword_id = create_resp.json()["id"]

    update_payload = {"enabled": False, "word": "updated-keyword"}
    response = await client.put(f"/keywords/{keyword_id}", json=update_payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["enabled"] is False
    assert data["word"] == "updated-keyword"


async def test_delete_keyword(client):
    create_resp = await client.post("/keywords", json=valid_keyword_payload)
    keyword_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/keywords/{keyword_id}")
    assert delete_resp.status_code == status.HTTP_204_NO_CONTENT

    get_resp = await client.get(f"/keywords/{keyword_id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND
