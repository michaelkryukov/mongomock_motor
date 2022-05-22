import bson
import pytest
from datetime import datetime, timezone
from pymongo import ReplaceOne
from mongomock_motor import AsyncMongoMockClient


@pytest.mark.anyio
async def test_workflow():
    collection = AsyncMongoMockClient()['tests']['test']

    result = await collection.insert_one({'a': 1})
    assert result.inserted_id
    doc_id = result.inserted_id

    result = await collection.update_one({'a': 1}, {'$set': {'b': 1}, '$inc': {'a': 1}})
    assert result.modified_count == 1

    result = await collection.update_one({'a': 1}, {'$set': {'b': 100}})
    assert result.modified_count == 0

    result = await collection.update_one({'_id': doc_id}, {'$inc': {'a': 1}})
    assert result.modified_count == 1

    docs = await collection.find({'a': 3}).to_list(None)
    assert len(docs) == 1
    assert docs[0]['_id'] == doc_id
    assert docs[0]['a'] == 3
    assert docs[0]['b'] == 1

    pipeline = [{'$match': {'a': 3}}]
    docs = await collection.aggregate(pipeline).to_list(None)
    assert len(docs) == 1
    assert docs[0]['_id'] == doc_id
    assert docs[0]['a'] == 3
    assert docs[0]['b'] == 1


@pytest.mark.anyio
async def test_tz_awareness():
    tz_aware_date = datetime(2022, 4, 26, tzinfo=timezone.utc)

    # Naive
    collection = AsyncMongoMockClient()['tests']['test']
    await collection.insert_one({'d': tz_aware_date})
    result = await collection.find_one()
    assert result['d'].tzinfo is None

    # Aware
    collection = AsyncMongoMockClient(tz_aware=True)['tests']['test']
    await collection.insert_one({'d': tz_aware_date})
    result = await collection.find_one()
    assert result['d'].tzinfo.__class__ is bson.tz_util.FixedOffset


@pytest.mark.anyio
async def test_bulk_write():
    collection = AsyncMongoMockClient()['tests']['test']
    result = await collection.bulk_write([
        ReplaceOne(
            filter={'_id': 1},
            replacement={'_id': 1},
            upsert=True
        )
    ])
    assert result.bulk_api_result['nUpserted'] == 1
