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
    doc_1 = {'i': 1}
    doc_2 = {'i': 2}

    # Insert sample documents into database in reverse order
    await collection.insert_one(doc_2)
    await collection.insert_one(doc_1)
    docs = collection.aggregate([{'$sort': {'i': 1}}])  # Sort to check order

    document_1 = await docs.next()
    document_2 = await docs.next()

    with pytest.raises(StopAsyncIteration):  # Assert error when iterator is exhausted
        await docs.next()
    assert [document_1, document_2] == [doc_1, doc_2]
