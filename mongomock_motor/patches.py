from mongomock import DuplicateKeyError, helpers


def _provide_error_details(collection, data, exception):
    if not isinstance(exception, DuplicateKeyError):
        return exception

    for index in collection._store.indexes.values():
        if not index.get('unique'):
            continue

        is_sparse = index.get('sparse')

        find_kwargs = {}
        for key, _ in index.get('key'):
            try:
                find_kwargs[key] = helpers.get_value_by_dot(data, key)
            except KeyError:
                find_kwargs[key] = None

        if is_sparse and set(find_kwargs.values()) == {None}:
            continue

        found_documents = list(collection._iter_documents(find_kwargs))
        if len(found_documents) > 0:
            return DuplicateKeyError(
                'E11000 Duplicate Key Error',
                11000,
                {
                    'keyValue': find_kwargs,
                    'keyPattern': dict(index.get('key')),
                },
                None,
            )

    return exception


def _patch_collection_internals(collection):
    """
    # Details for DuplicateKeyError

    Adds details with 'keyPattern' and 'keyValue' when
    raising DuplicateKeyError from _insert
    https://github.com/mongomock/mongomock/issues/773
    """
    _insert = collection._insert

    def insert(data, *args, **kwargs):
        try:
            return _insert(data, *args, **kwargs)
        except DuplicateKeyError as exc:
            raise _provide_error_details(collection, data, exc)

    collection._insert = insert

    return collection
