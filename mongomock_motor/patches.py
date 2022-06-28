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


def _patch_insert(collection):
    """
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


def _normalize_strings(obj):
    if isinstance(obj, list):
        return [_normalize_strings(v) for v in obj]

    if isinstance(obj, dict):
        return {_normalize_strings(k): _normalize_strings(v) for k, v in obj.items()}

    if isinstance(obj, str):
        return str(obj)

    return obj


def _patch_iter_documents(collection):
    """
    When using beanie, keys can have "ExpressionField" type,
    that is inherited from "str". Looks like pymongo works ok
    with that, so we should be too.
    """
    _iter_documents = collection._iter_documents

    def iter_documents(filter):
        return _iter_documents(_normalize_strings(filter))

    collection._iter_documents = iter_documents

    return collection


def _patch_collection_internals(collection):
    collection = _patch_insert(collection)
    collection = _patch_iter_documents(collection)
    return collection


__all__ = ['_patch_collection_internals']
