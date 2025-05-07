import pytest
from pymongo import ASCENDING, DESCENDING

from mongomock_motor import AsyncMongoMockClient


@pytest.mark.anyio
async def test_list_indexes():
    collection = AsyncMongoMockClient()['tests']['test']

    # No indexes by default
    assert await collection.list_indexes().to_list(length=None) == []

    # Insert sample document
    await collection.insert_one({'field1': 1, 'field2': 2})

    # Initially only _id index exists
    docs = await collection.list_indexes().to_list(length=None)
    assert len(docs) == 1
    assert docs[0]['name'] == '_id_'

    # Create multiple indexes
    await collection.create_index([('field1', ASCENDING)])
    await collection.create_index([('field2', DESCENDING)])

    # Verify all indexes are listed
    docs = await collection.list_indexes().to_list(length=None)
    assert len(docs) == 3

    # Verify index names and keys
    index_names = {doc['name'] for doc in docs}
    assert index_names == {'_id_', 'field1_1', 'field2_-1'}


@pytest.mark.anyio
async def test_list_indexes_context_manager():
    collection = AsyncMongoMockClient()['tests']['test']

    await collection.insert_one({'key': 'value'})

    indexes = []

    async for index in collection.list_indexes():
        indexes.append(index)

    assert len(indexes) == 1
    assert indexes[0]['name'] == '_id_'
