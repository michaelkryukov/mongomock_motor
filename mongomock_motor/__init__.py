from functools import wraps
import importlib
from mongomock import MongoClient
from .patches import _patch_collection_internals


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
@with_cursor_chaining_methods('__cursor', [
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
])
class AsyncCursor():
    def __init__(self, cursor):
        self.__cursor = cursor

    def __getattr__(self, name):
        return getattr(self.__cursor, name)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.__cursor)
        except StopIteration:
            raise StopAsyncIteration()

    async def to_list(self, *args, **kwargs):
        return list(self.__cursor)


@masquerade_class('motor.motor_asyncio.AsyncIOMotorCollection')
@with_async_methods('__collection', [
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
])
class AsyncMongoMockCollection():
    def __init__(self, collection):
        self.__collection = collection

    def __getattr__(self, name):
        return getattr(self.__collection, name)

    def find(self, *args, **kwargs) -> AsyncCursor:
        return AsyncCursor(self.__collection.find(*args, **kwargs))

    def aggregate(self, *args, **kwargs) -> AsyncCursor:
        return AsyncCursor(self.__collection.aggregate(*args, **kwargs))


@masquerade_class('motor.motor_asyncio.AsyncIOMotorDatabase')
@with_async_methods('__database', [
    'create_collection',
    'dereference',
    'drop_collection',
    'list_collection_names',
    'validate_collection',
])
class AsyncMongoMockDatabase():
    def __init__(self, database, mock_build_info=None):
        self.__database = database
        self.__build_info = mock_build_info or {'ok': 1.0, 'version': '5.0.5'}

    def get_collection(self, *args, **kwargs):
        return AsyncMongoMockCollection(
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
            if args == ({'buildInfo': 1},) and not kwargs:
                return self.__build_info
            raise

    def __getitem__(self, name):
        return self.get_collection(name)

    def __getattr__(self, name):
        if name in dir(self.__database):
            return getattr(self.__database, name)

        return self.get_collection(name)


@masquerade_class('motor.motor_asyncio.AsyncIOMotorClient')
@with_async_methods('__client', [
    'drop_database',
    'list_database_names',
    'list_databases',
    'server_info',
])
class AsyncMongoMockClient():
    def __init__(self, *args, mock_build_info=None, **kwargs):
        self.__client = MongoClient(*args, **kwargs)
        self.__build_info = mock_build_info

    def get_database(self, *args, **kwargs):
        return AsyncMongoMockDatabase(
            self.__client.get_database(*args, **kwargs),
            mock_build_info=self.__build_info,
        )

    def __getitem__(self, name):
        return self.get_database(name)

    def __getattr__(self, name):
        if name in dir(self.__client):
            return getattr(self.__client, name)

        return self.get_database(name)
