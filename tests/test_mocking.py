from unittest.mock import patch
from bson import ObjectId
from pymongo.results import UpdateResult
import pytest
from mongomock_motor import AsyncMongoMockClient


@pytest.mark.anyio
async def sample_function(collection):
    result = await collection.update_one(
        filter={'_id': ObjectId()},
        update={'$set': {'field': 'value'}},
        upsert=True,
    )

    if result.acknowledged is False:
        raise RuntimeError()


def async_wrapper(value):
    async def wrapper(*args, **kwargs):
        return value
    return wrapper


@pytest.mark.anyio
async def test_patch():
    collection = AsyncMongoMockClient()['test']['test']

    with patch('mongomock_motor.AsyncMongoMockCollection.update_one', new=async_wrapper(UpdateResult({}, False))):
        with pytest.raises(RuntimeError):
            await sample_function(collection)


@pytest.mark.anyio
async def test_patch_object():
    collection = AsyncMongoMockClient()['test']['test']

    with patch.object(collection, 'update_one', new=async_wrapper(UpdateResult({}, False))):
        with pytest.raises(RuntimeError):
            await sample_function(collection)
