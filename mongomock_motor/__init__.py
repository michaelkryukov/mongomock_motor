from functools import wraps
import importlib
from mongomock import MongoClient


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


@masquerade_class('motor.motor_asyncio.AsyncIOMotorCursor')
class AsyncCursor():
    PROXIED_CURSOR_CHAINING_METHODS = [
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
    ]

    def __init__(self, cursor):
        self.__cursor = cursor

        for method_name in self.PROXIED_CURSOR_CHAINING_METHODS:
            def make_wrapper(method_name):
                def wrapper(*args, **kwargs):
                    getattr(self.__cursor, method_name)(*args, **kwargs)
                    return self
                return wrapper

            setattr(self, method_name, make_wrapper(method_name))

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
class AsyncMongoMockCollection():
    ASYNC_METHODS = [
        'count_documents',
        'count',
        'create_index',
        'create_indexes',
        'delete_many',
        'delete_one',
        'drop',
        'ensure_index',
        'estimated_document_count',
        'find_and_modify',
        'find_one_and_delete',
        'find_one_and_replace',
        'find_one_and_update',
        'find_one',
        'index_information',
        'insert_many',
        'insert_one',
        'map_reduce',
        'replace_one',
        'save',
        'update_many',
        'update_one',
    ]

    def __init__(self, collection):
        self.__collection = collection

        for method_name in self.ASYNC_METHODS:
            def make_wrapper(method_name):
                async def wrapper(*args, **kwargs):
                    return getattr(self.__collection, method_name)(*args, **kwargs)
                return wrapper

            setattr(self, method_name, make_wrapper(method_name))

    def __getattr__(self, name):
        return getattr(self.__collection, name)

    def find(self, *args, **kwargs) -> AsyncCursor:
        return AsyncCursor(self.__collection.find(*args, **kwargs))

    def aggregate(self, *args, **kwargs) -> AsyncCursor:
        return AsyncCursor(self.__collection.aggregate(*args, **kwargs))


@masquerade_class('motor.motor_asyncio.AsyncIOMotorDatabase')
class AsyncMongoMockDatabase():
    def __init__(self, database, mock_build_info=None):
        self.__database = database
        self.__collections = {}
        self.__build_info = mock_build_info or {'ok': 1.0, 'version': '5.0.5'}

    async def command(self, *args, **kwargs):
        try:
            return getattr(self.__database, 'command')(*args, **kwargs)
        except NotImplementedError:
            if args == ({'buildInfo': 1},) and not kwargs:
                return self.__build_info
            raise

    def __getitem__(self, name):
        return getattr(self, name)

    def __getattr__(self, name):
        if name not in self.__collections:
            self.__collections[name] = AsyncMongoMockCollection(
                self.__database[name],
            )
        return self.__collections[name]


@masquerade_class('motor.motor_asyncio.AsyncIOMotorClient')
class AsyncMongoMockClient():
    def __init__(self, *args, mock_build_info=None, **kwargs):
        self.__client = MongoClient()
        self.__databases = {}
        self.__build_info = mock_build_info

    def __getitem__(self, name):
        return getattr(self, name)

    def __getattr__(self, name):
        if name not in self.__databases:
            self.__databases[name] = AsyncMongoMockDatabase(
                self.__client[name],
                mock_build_info=self.__build_info,
            )
        return self.__databases[name]
