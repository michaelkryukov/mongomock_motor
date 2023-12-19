import pytest
from mongomock_motor import AsyncMongoMockClient, enabled_gridfs_integration
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
import io


@pytest.mark.anyio
async def test_gridfs():
    with enabled_gridfs_integration():
        fs = AsyncIOMotorGridFSBucket(AsyncMongoMockClient()['db'])

        file_name = 'file.txt'
        file_bytes = b'sup'
        file_id = await fs.upload_from_stream(file_name, file_bytes)

        with io.BytesIO() as buffer:
            await fs.download_to_stream(file_id, buffer)
            assert buffer.getvalue() == file_bytes
