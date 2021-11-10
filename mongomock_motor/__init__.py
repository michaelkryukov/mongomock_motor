from mongomock import MongoClient


class AsyncCursor():
    def __init__(self, cursor):
        self.__cursor = cursor

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.__cursor)
        except StopIteration:
            raise StopAsyncIteration()

    async def to_list(self, *args, **kwargs):
        return list(self.__cursor)


class AsyncMongoMockCollection():
    ASYNC_METHODS = [
        "find_one",
        "find_one_and_delete",
        "find_one_and_replace",
        "find_one_and_update",
        "find_and_modify",
        "save",
        "delete_one",
        "delete_many",
        "count",
        "insert_one",
        "insert_many",
        "update_one",
        "update_many",
        "replace_one",
        "count_documents",
        "estimated_document_count",
        "drop",
        "create_index",
        "ensure_index",
        "map_reduce",
    ]

    def __init__(self, collection):
        self.__collection = collection

        for method_name in self.ASYNC_METHODS:
            def make_wrapper(method_name):
                async def wrapper(*args, **kwargs):
                    return getattr(self.__collection, method_name)(*args, **kwargs)
                return wrapper

            setattr(self, method_name, make_wrapper(method_name))

    def find(self, *args, **kwargs) -> AsyncCursor:
        return AsyncCursor(self.__collection.find(*args, **kwargs))


class AsyncMongoMockDatabase():
    def __init__(self, database):
        self.__database = database
        self.__collections = {}

    def __getitem__(self, name):
        return getattr(self, name)

    def __getattr__(self, name):
        if name not in self.__collections:
            self.__collections[name] = AsyncMongoMockCollection(self.__database[name])
        return self.__collections[name]


class AsyncMongoMockClient():
    def __init__(self):
        self.__client = MongoClient()
        self.__databases = {}

    def __getitem__(self, name):
        return getattr(self, name)

    def __getattr__(self, name):
        if name not in self.__databases:
            self.__databases[name] = AsyncMongoMockDatabase(self.__client[name])
        return self.__databases[name]
