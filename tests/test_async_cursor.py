import pymongo
import pytest

from mongomock_motor import AsyncMongoMockClient

EXPECTED_DOCUMENTS_COUNT = 10


@pytest.mark.anyio
async def test_closeable():
    collection = AsyncMongoMockClient()['tests']['test']

    # Insert sample documents into database
    await collection.insert_many([{'i': i} for i in range(EXPECTED_DOCUMENTS_COUNT)])

    # Create cursor
    cursor = collection.find()

    # Close cursor
    await cursor.close()

    # Closing of already closed cursor don't trigger errors
    await cursor.close()

    # Create command cursor
    command_cursor = collection.aggregate([])

    # Close cursor
    await command_cursor.close()

    # Closing of already closed cursor don't trigger errors
    await command_cursor.close()


@pytest.mark.anyio
async def test_skip_and_limit():
    collection = AsyncMongoMockClient()['tests']['test']

    # Insert sample documents into database
    await collection.insert_many([{'i': i} for i in range(EXPECTED_DOCUMENTS_COUNT)])

    # Query without limitations
    docs = await collection.find().to_list(None)
    assert len(docs) == EXPECTED_DOCUMENTS_COUNT

    # Query with limit
    docs = await collection.find().limit(2).to_list(None)
    assert len(docs) == 2

    # Query with skip
    docs = await collection.find().skip(2).to_list(None)
    assert len(docs) == EXPECTED_DOCUMENTS_COUNT - 2

    # Query with limit and skip
    docs = await collection.find().skip(2).limit(2).to_list(None)
    assert len(docs) == 2

    # Query with limit, skip and sort
    docs = await (
        collection.find(projection={'_id': 0})
        .skip(2)
        .limit(2)
        .sort('i', pymongo.DESCENDING)
        .to_list(None)
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

    docs = await collection.aggregate([{'$match': {'i': 0}}]).to_list(None)
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
        for _ in cursor:  # type: ignore
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
    indexes = await collection.list_indexes().to_list(None)
    assert len(indexes) == 1

    # Create a second index on the field 'i'
    await collection.create_index([('i', pymongo.DESCENDING)])

    # Check that there are now two indexes
    indexes = await collection.list_indexes().to_list(None)
    assert len(indexes) == 2


@pytest.mark.anyio
async def test_distinct():
    collection = AsyncMongoMockClient()['tests']['test']

    # Insert sample documents with duplicate values
    await collection.insert_many(
        [
            {'category': 'A', 'value': 1},
            {'category': 'A', 'value': 2},
            {'category': 'B', 'value': 3},
            {'category': 'B', 'value': 4},
            {'category': 'C', 'value': 5},
        ]
    )

    # Test distinct on category field
    categories = await collection.find().distinct('category')
    assert sorted(categories) == ['A', 'B', 'C']

    # Test distinct with query
    values = await collection.find({'category': 'A'}).distinct('value')
    assert sorted(values) == [1, 2]

    # Test distinct on non-existent field
    empty = await collection.find().distinct('non_existent')
    assert empty == []

    # Test distinct on nested field
    await collection.insert_many(
        [
            {'nested': {'field': 'X'}},
            {'nested': {'field': 'Y'}},
            {'nested': {'field': 'X'}},
        ]
    )
    nested_values = await collection.find().distinct('nested.field')
    assert sorted(nested_values) == ['X', 'Y']
