import pytest

from mongomock_motor import AsyncMongoMockClient


@pytest.mark.anyio
async def test_hashing_is_possible():
    hash(AsyncMongoMockClient())
    hash(AsyncMongoMockClient()['database'])
    hash(AsyncMongoMockClient()['database']['collection'])


@pytest.mark.anyio
async def test_hashing_is_stable():
    assert hash(AsyncMongoMockClient()) == hash(AsyncMongoMockClient())
    assert hash(AsyncMongoMockClient('localhost')) == hash(
        AsyncMongoMockClient('not.localhost')
    )
    assert hash(AsyncMongoMockClient()['database1']) == hash(
        AsyncMongoMockClient()['database1']
    )
    assert hash(AsyncMongoMockClient()['database1']) != hash(
        AsyncMongoMockClient()['database2']
    )
