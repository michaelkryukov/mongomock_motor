import pytest

from mongomock_motor import AsyncMongoMockClient


@pytest.mark.anyio
async def test_command_buildinfo():
    database = AsyncMongoMockClient().get_database('tests')

    assert await database.command('buildinfo')
    assert await database.command({'buildinfo': 1})


@pytest.mark.anyio
async def test_unknown_command():
    database = AsyncMongoMockClient().get_database('tests')

    with pytest.raises(NotImplementedError):
        await database.command('apldjnkasd')
