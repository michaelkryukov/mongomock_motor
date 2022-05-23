import pytest
from mongomock_motor import AsyncMongoMockClient


@pytest.mark.anyio
async def test_lists():
    client = AsyncMongoMockClient()

    collection1 = client['tests-1']['test-1']
    await collection1.insert_one({'a': 1})

    collection2 = client['tests-2']['test-2']
    await collection2.insert_one({'a': 2})

    collection2 = client['tests-2']['test-2-copy']
    await collection2.insert_one({'a': 2})

    assert await client.list_database_names() == ['tests-1', 'tests-2']
    assert await client['tests-1'].list_collection_names() == ['test-1']
    assert await client['tests-2'].list_collection_names() == ['test-2', 'test-2-copy']
