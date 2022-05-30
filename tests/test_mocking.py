from unittest.mock import patch, AsyncMock
from bson import ObjectId
from pymongo.results import UpdateResult
import pytest
from mongomock_motor import AsyncMongoMockClient


async def sample_function(collection):
    result = await collection.update_one(
        filter={'_id': ObjectId()},
        update={'$set': {'field': 'value'}},
        upsert=True,
    )

    if result.acknowledged is False:
        raise RuntimeError()


@pytest.mark.asyncio
async def test_patch():
    collection = AsyncMongoMockClient()['test']['test']

    with patch('mongomock_motor.AsyncMongoMockCollection.update_one', AsyncMock(return_value=UpdateResult({}, False))):
        with pytest.raises(RuntimeError):
            await sample_function(collection)


@pytest.mark.asyncio
async def test_patch_object():
    collection = AsyncMongoMockClient()['test']['test']

    with patch.object(collection, 'update_one', AsyncMock(return_value=UpdateResult({}, False))):
        with pytest.raises(RuntimeError):
            await sample_function(collection)
