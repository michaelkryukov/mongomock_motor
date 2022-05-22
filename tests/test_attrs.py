from pymongo import ReadPreference
import pytest
from mongomock_motor import AsyncMongoMockClient


@pytest.mark.anyio
async def test_attrs():
    client = AsyncMongoMockClient()
    database = client.get_database('tests')
    collection = database.get_collection('test')
    await collection.insert_one({'a': 1})

    assert await client['tests']['test'].find_one(projection={'_id': 0, 'a': 1}) == {'a': 1}
    assert await client.tests.test.find_one(projection={'_id': 0, 'a': 1}) == {'a': 1}
    assert await collection.find_one(projection={'_id': 0, 'a': 1}) == {'a': 1}

    database = client.get_database('tests', read_preference=ReadPreference.SECONDARY)
    assert await database.test.find_one(projection={'_id': 0, 'a': 1}) == {'a': 1}
