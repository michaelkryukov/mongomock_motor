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
