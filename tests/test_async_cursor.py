import pymongo
import pytest
from mongomock_motor import AsyncMongoMockClient


EXPECTED_DOCUMENTS_COUNT = 10


@pytest.mark.anyio
async def test_skip_and_limit():
    collection = AsyncMongoMockClient()['tests']['test']

    # Insert sample documents into database
    await collection.insert_many([{'i': i} for i in range(EXPECTED_DOCUMENTS_COUNT)])

    # Query without limitations
    docs = await collection.find().to_list()
    assert len(docs) == EXPECTED_DOCUMENTS_COUNT

    # Query with limit
    docs = await collection.find().limit(2).to_list()
    assert len(docs) == 2

    # Query with skip
    docs = await collection.find().skip(2).to_list()
    assert len(docs) == EXPECTED_DOCUMENTS_COUNT - 2

    # Query with limit and skip
    docs = await collection.find().skip(2).limit(2).to_list()
    assert len(docs) == 2

    # Query with limit, skip and sort
    docs = await (
        collection
        .find(projection={'_id': 0})
        .skip(2)
        .limit(2)
        .sort('i', pymongo.DESCENDING)
        .to_list()
    )

    assert len(docs) == 2
    assert docs == [
        {'i': EXPECTED_DOCUMENTS_COUNT - 3},
        {'i': EXPECTED_DOCUMENTS_COUNT - 4},
    ]


@pytest.mark.anyio
async def test_aggregate():
    collection = AsyncMongoMockClient()['tests']['test']

    # Insert sample documents into database
    await collection.insert_many([{'i': i} for i in range(EXPECTED_DOCUMENTS_COUNT)])

    docs = await collection.aggregate([{'$match': {'i': 0}}]).to_list()
    assert len(docs) == 1


@pytest.mark.anyio
async def test_next():
    collection = AsyncMongoMockClient()['tests']['test']

    # Insert sample documents into database
    sample_docs = [{'i': i} for i in range(EXPECTED_DOCUMENTS_COUNT)]
    await collection.insert_many(sample_docs)

    # Create cursor with sorted docs
    cursor = collection.find(sort=[('i', 1)])

    # Query docs using "next" coroutine
    docs = []
    for _ in range(EXPECTED_DOCUMENTS_COUNT):
        docs.append(await cursor.next())

    # Check that cursor is exhausted
    with pytest.raises(StopAsyncIteration):
        await cursor.next()

    # Check docs are correct
    assert docs == sample_docs


@pytest.mark.anyio
async def test_async_for():
    collection = AsyncMongoMockClient()['tests']['test']

    # Insert sample documents into database
    sample_docs = [{'i': i} for i in range(EXPECTED_DOCUMENTS_COUNT)]
    await collection.insert_many(sample_docs)

    # Create cursor with sorted docs
    cursor = collection.aggregate([{'$sort': {'i': 1}}])

    # Check that plain for-loop won't work
    with pytest.raises(TypeError):
        for _ in cursor:
            pass

    # Iterate over cursor with for-loop
    docs = []
    async for doc in cursor:
        docs.append(doc)

    # Check that cursor is exhausted
    with pytest.raises(StopAsyncIteration):
        await cursor.next()

    # Check docs are correct
    assert docs == sample_docs


@pytest.mark.anyio
async def test_list_indexes():
    collection = AsyncMongoMockClient()['tests']['test']

    # Insert sample documents into database
    await collection.insert_many([{'i': i} for i in range(EXPECTED_DOCUMENTS_COUNT)])

    # Check that there is one default '_id' index
    indexes = await collection.list_indexes().to_list()
    assert len(indexes) == 1

    # Create a second index on the field 'i'
    await collection.create_index([('i', pymongo.DESCENDING)])

    # Check that there are now two indexes
    indexes = await collection.list_indexes().to_list()
    assert len(indexes) == 2
