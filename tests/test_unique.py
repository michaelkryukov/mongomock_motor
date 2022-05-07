import pytest
from pymongo.errors import DuplicateKeyError
from mongomock_motor import AsyncMongoMockClient


@pytest.mark.anyio
async def test_unique_while_inserting():
    collection = AsyncMongoMockClient()['tests']['test']

    await collection.create_index('a', unique=True)

    await collection.insert_one({'a': 1})

    with pytest.raises(DuplicateKeyError):
        await collection.insert_one({'a': 1})

    assert len(await collection.find({}).to_list(None)) == 1


@pytest.mark.anyio
async def test_unique_while_creating_index():
    collection = AsyncMongoMockClient()['tests']['test']

    await collection.insert_one({'a': 1})
    await collection.insert_one({'a': 1})

    with pytest.raises(DuplicateKeyError):
        await collection.create_index('a', unique=True)

    assert len(await collection.find({}).to_list(None)) == 2
