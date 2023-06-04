import pytest
from mongomock import MongoClient

from mongomock_motor import AsyncMongoMockClient


@pytest.mark.anyio
async def test_different_mongo_clients():
    # Create clients
    client = MongoClient()
    async_client = AsyncMongoMockClient()

    # Get collections
    collection = client['tests']['test']
    async_collection = async_client['tests']['test']

    # Insert sample documents into databases
    collection.insert_one({'s': 1})
    await async_collection.insert_one({'a': 1})

    # Test clients are different
    assert collection.count_documents({}) == 1
    assert await async_collection.count_documents({}) == 1


@pytest.mark.anyio
async def test_shared_mongo_client():
    # Create clients
    client = MongoClient()
    async_client = AsyncMongoMockClient(mock_mongo_client=client)

    # Get collections
    collection = client['tests']['test']
    async_collection = async_client['tests']['test']

    # Insert sample documents into database
    collection.insert_one({'s': 1})
    await async_collection.insert_one({'a': 1})

    # Test client are shared
    assert collection.count_documents({}) == 2
    assert await async_collection.count_documents({}) == 2
