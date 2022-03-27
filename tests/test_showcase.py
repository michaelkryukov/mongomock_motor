import pytest
from mongomock_motor import AsyncMongoMockClient


@pytest.mark.anyio
async def test_mock_client():
    collection = AsyncMongoMockClient()['tests']['test']

    assert await collection.find({}).to_list(None) == []

    result = await collection.insert_one({'a': 1})
    assert result.inserted_id

    assert len(await collection.find({}).to_list(None)) == 1
