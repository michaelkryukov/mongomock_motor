from datetime import datetime, timezone

import bson
import bson.tz_util
import pytest
from pymongo import DeleteMany, InsertOne, ReplaceOne, UpdateOne

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
    assert result
    assert result['d'].tzinfo is None

    # Aware
    collection = AsyncMongoMockClient(tz_aware=True)['tests']['test']
    await collection.insert_one({'d': tz_aware_date})
    result = await collection.find_one()
    assert result
    assert result['d'].tzinfo.__class__ is bson.tz_util.FixedOffset


@pytest.mark.anyio
async def test_bulk_write():
    collection = AsyncMongoMockClient()['tests']['test']

    write_result = await collection.bulk_write(
        [
            InsertOne({'_id': 1}),
            DeleteMany({}),
            InsertOne({'_id': 1}),
            InsertOne({'_id': 2}),
            InsertOne({'_id': 3}),
            UpdateOne({'_id': 1}, {'$set': {'foo': 'bar'}}),
            UpdateOne({'_id': 4}, {'$inc': {'j': 1}}, upsert=True),
            ReplaceOne({'j': 1}, {'j': 2}),
        ],
    )

    assert write_result.bulk_api_result['nInserted'] == 4
    assert write_result.bulk_api_result['nMatched'] == 2
    assert write_result.bulk_api_result['nModified'] == 2
    assert write_result.bulk_api_result['nUpserted'] == 1

    documents = await collection.find({}).to_list(None)

    assert documents == [
        {'_id': 1, 'foo': 'bar'},
        {'_id': 2},
        {'_id': 3},
        {'_id': 4, 'j': 2},
    ]
