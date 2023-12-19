import asyncio
import importlib
from contextlib import ExitStack, contextmanager
from functools import wraps
from unittest.mock import patch

from mongomock import Collection as MongoMockCollection
from mongomock import Database as MongoMockDatabase
from mongomock import MongoClient
from mongomock.gridfs import _create_grid_out_cursor
from pymongo.database import Database as PyMongoDatabase

from .patches import _patch_client_internals, _patch_collection_internals


def masquerade_class(name):
    module_name, target_name = name.rsplit('.', 1)

    try:
        target = getattr(importlib.import_module(module_name), target_name)
    except Exception:
        return lambda cls: cls

    def decorator(cls):
        @wraps(target, updated=())
        class Wrapper(cls):
            @property
            def __class__(self):
                return target

        return Wrapper

    return decorator


def with_async_methods(source, async_methods):
    def decorator(cls):
        for method_name in async_methods:

            def make_wrapper(method_name):
                async def wrapper(self, *args, **kwargs):
                    proxy_source = self.__dict__.get(f'_{cls.__name__}{source}')
                    return getattr(proxy_source, method_name)(*args, **kwargs)

                return wrapper

            setattr(cls, method_name, make_wrapper(method_name))

        return cls

    return decorator


def with_cursor_chaining_methods(source, chaining_methods):
    def decorator(cls):
        for method_name in chaining_methods:

            def make_wrapper(method_name):
                def wrapper(self, *args, **kwargs):
                    proxy_source = self.__dict__.get(f'_{cls.__name__}{source}')
                    getattr(proxy_source, method_name)(*args, **kwargs)
                    return self

                return wrapper

            setattr(cls, method_name, make_wrapper(method_name))

        return cls

    return decorator


@masquerade_class('motor.motor_asyncio.AsyncIOMotorCursor')
@with_cursor_chaining_methods(
    '__cursor',
    [
        'add_option',
        'allow_disk_use',
        'collation',
        'comment',
        'hint',
        'limit',
        'max_await_time_ms',
        'max_scan',
        'max_time_ms',
        'max',
        'min',
        'remove_option',
        'skip',
        'sort',
        'where',
    ],
)
class AsyncCursor:
    def __init__(self, cursor):
        self.__cursor = cursor

    def __getattr__(self, name):
        return getattr(self.__cursor, name)

    def __aiter__(self):
        return self

    async def next(self):
        try:
            return next(self.__cursor)
        except StopIteration:
            raise StopAsyncIteration()

    __anext__ = next

    def clone(self):
        return AsyncCursor(self.__cursor.clone())

    async def distinct(self, *args, **kwargs):
        return self.__cursor.distinct(*args, **kwargs)

    async def to_list(self, *args, **kwargs):
        return list(self.__cursor)


@masquerade_class('motor.motor_asyncio.AsyncIOMotorLatentCommandCursor')
class AsyncLatentCommandCursor:
    def __init__(self, cursor):
        self.__cursor = cursor

    def __getattr__(self, name):
        return getattr(self.__cursor, name)

    def __aiter__(self):
        return self

    async def next(self):
        try:
            return next(self.__cursor)
        except StopIteration:
            raise StopAsyncIteration()

    __anext__ = next

    async def to_list(self, *args, **kwargs):
        return list(self.__cursor)


@masquerade_class('motor.motor_asyncio.AsyncIOMotorCollection')
@with_async_methods(
    '__collection',
    [
        'bulk_write',
        'count_documents',
        'count',  # deprecated
        'create_index',
        'create_indexes',
        'delete_many',
        'delete_one',
        'drop_index',
        'drop_indexes',
        'drop',
        'distinct',
        'ensure_index',
        'estimated_document_count',
        'find_and_modify',  # deprecated
        'find_one_and_delete',
        'find_one_and_replace',
        'find_one_and_update',
        'find_one',
        'index_information',
        'inline_map_reduce',
        'insert_many',
        'insert_one',
        'map_reduce',
        'options',
        'reindex',
        'rename',
        'replace_one',
        'save',
        'update_many',
        'update_one',
    ],
)
class AsyncMongoMockCollection:
    def __init__(self, database, collection):
        self.database = database
        self.__collection = collection

    def get_io_loop(self):
        return self.database.get_io_loop()

    def __eq__(self, other):
        return self.__collection == other.__collection

    def __getattr__(self, name):
        return getattr(self.__collection, name)

    def find(self, *args, **kwargs) -> AsyncCursor:
        return AsyncCursor(self.__collection.find(*args, **kwargs))

    def aggregate(self, *args, **kwargs) -> AsyncLatentCommandCursor:
        return AsyncLatentCommandCursor(self.__collection.aggregate(*args, **kwargs))

    def list_indexes(self, *args, **kwargs) -> AsyncCursor:
        return AsyncCursor(self.__collection.list_indexes(*args, **kwargs))


@masquerade_class('motor.motor_asyncio.AsyncIOMotorDatabase')
@with_async_methods(
    '__database',
    [
        'create_collection',
        'dereference',
        'drop_collection',
        'list_collection_names',
        'validate_collection',
    ],
)
class AsyncMongoMockDatabase:
    def __init__(self, client, database, mock_build_info=None):
        self.client = client
        self.__database = database
        self.__build_info = mock_build_info or {
            'ok': 1.0,
            'version': '5.0.5',
            'versionArray': [5, 0, 5],
        }

    @property
    def delegate(self):
        return self.__database

    def get_io_loop(self):
        return self.client.get_io_loop()

    def get_collection(self, *args, **kwargs):
        return AsyncMongoMockCollection(
            self,
            _patch_collection_internals(
                self.__database.get_collection(*args, **kwargs),
            ),
        )

    def aggregate(self, *args, **kwargs) -> AsyncCursor:
        return AsyncCursor(self.__database.aggregate(*args, **kwargs))

    async def command(self, *args, **kwargs):
        try:
            return getattr(self.__database, 'command')(*args, **kwargs)
        except NotImplementedError:
            if not args:
                raise
            if isinstance(args[0], str) and args[0].lower() == 'buildinfo':
                return self.__build_info
            if (
                isinstance(args[0], dict)
                and args[0]
                and list(args[0])[0].lower() == 'buildinfo'
            ):
                return self.__build_info
            raise

    def __eq__(self, other):
        return self.__database == other.__database

    def __getitem__(self, name):
        return self.get_collection(name)

    def __getattr__(self, name):
        if name in dir(self.__database):
            return getattr(self.__database, name)

        return self.get_collection(name)


@masquerade_class('motor.motor_asyncio.AsyncIOMotorClient')
@with_async_methods(
    '__client',
    [
        'drop_database',
        'list_database_names',
        'list_databases',
        'server_info',
    ],
)
class AsyncMongoMockClient:
    def __init__(
        self,
        *args,
        mock_build_info=None,
        mock_mongo_client=None,
        mock_io_loop=None,
        **kwargs,
    ):
        self.__client = _patch_client_internals(
            mock_mongo_client or MongoClient(*args, **kwargs)
        )
        self.__build_info = mock_build_info
        self.__io_loop = mock_io_loop

    def get_io_loop(self):
        return self.__io_loop or asyncio.get_event_loop()

    def get_database(self, *args, **kwargs):
        return AsyncMongoMockDatabase(
            self,
            self.__client.get_database(*args, **kwargs),
            mock_build_info=self.__build_info,
        )

    def __eq__(self, other):
        return self.__client == other.__client

    def __getitem__(self, name):
        return self.get_database(name)

    def __getattr__(self, name):
        if name in dir(self.__client):
            return getattr(self.__client, name)

        return self.get_database(name)


@contextmanager
def enabled_gridfs_integration():
    with ExitStack() as stack:
        stack.enter_context(
            patch('gridfs.Database', (PyMongoDatabase, MongoMockDatabase))
        )
        stack.enter_context(
            patch('gridfs.grid_file.Collection', (PyMongoDatabase, MongoMockCollection))
        )
        stack.enter_context(patch('gridfs.GridOutCursor', _create_grid_out_cursor))
        yield
