import pytest

from mongomock_motor import AsyncMongoMockClient


@pytest.mark.anyio
async def test_hashing_is_possible():
    hash(AsyncMongoMockClient())
    hash(AsyncMongoMockClient()['database'])
    hash(AsyncMongoMockClient()['database']['collection'])


@pytest.mark.anyio
async def test_hashing_is_stable():
    client1 = AsyncMongoMockClient()
    client2 = AsyncMongoMockClient()
    client3 = AsyncMongoMockClient('not.localhost')

    assert hash(client1) == hash(client2)
    assert hash(client1) != hash(client3)
    assert hash(client2) != hash(client3)

    assert hash(client1['database1']) == hash(client2['database1'])
    assert hash(client1['database1']) != hash(client2['database2'])
