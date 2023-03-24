from enum import Enum

import pytest
from mongo_thingy import AsyncThingy, connect
from pymongo.errors import DuplicateKeyError

from mongomock_motor import AsyncMongoMockClient


@pytest.mark.anyio
async def test_mongo_thingy():
    connect(client_cls=AsyncMongoMockClient)

    class Something(AsyncThingy):
        pass

    Something.add_index('field1', unique=True)
    await Something.create_indexes()

    something1 = Something(field1='A', field2=':)', related=[])
    await something1.save()

    # DuplicateKeyError should be raised when inserting
    with pytest.raises(
        DuplicateKeyError,
        match="^E11000 Duplicate Key Error, full error: {'keyValue': {'field1': 'A'}, 'keyPattern': {'field1': 1}}$",
    ):
        duplicate = Something(field1='A', field2=':)', related=[])
        await duplicate.save()

    something2 = Something(field1='B', field2=';)', related=[something1.id])
    await something2.save()

    # DuplicateKeyError should be raised when updating
    with pytest.raises(
        DuplicateKeyError,
        match="^E11000 Duplicate Key Error, full error: {'keyValue': {'field1': 'A'}, 'keyPattern': {'field1': 1}}$",
    ):
        something2.field1 = 'A'
        await something2.save()

    found = await Something.find_one({'field1': 'B'})
    assert found
    assert found.field1 == 'B'
    assert found.field2 == ';)'
    assert len(found.related) == 1


@pytest.mark.anyio
async def test_mongo_thingy_enums():
    connect(client_cls=AsyncMongoMockClient)

    class Importance(str, Enum):
        HIGH = 'high'
        LOW = 'low'

    class Something(AsyncThingy):
        pass

    something1 = Something(importance='high')
    await something1.save()

    assert await Something.count({'importance': Importance.HIGH})
