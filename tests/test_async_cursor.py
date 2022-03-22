import pytest
from mongomock_motor import AsyncMongoMockClient


@pytest.mark.anyio
async def test_skip():
    # Load 6 test documents to db
    document_count = 6
    collection = AsyncMongoMockClient()['tests']['test']
    await collection.insert_many(({'i': i} for i in range(document_count)))

    # calculate pagination
    page, length = 0, 2
    skip = page * length
    
    # count documents & assert against document_count
    count = await collection.count_documents({})
    assert count == document_count
    
    # retrieve cursor with filters to provide pagination
    cursor = collection.find().skip(skip).limit(length)
    
    # use to_list() & walk the cursor asserting chuncks of 2 per iteration
    for document in await cursor.to_list(length=length):
        assert len(document) == length