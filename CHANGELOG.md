# Changelog

# v0.0.5

- Make `AsyncCursor` more similar to `AsyncIOMotorCursor` (add support
    for `limit`, `skip`, `sort`, e.t.c.) + tests.

## v0.0.4

- Add limited support for `{buildInfo: 1}` command.
- Add attributes proxying for collections.
- Add tests for links (limited).
- Bump version for beanie, mongomock

## v0.0.3

- Add support for `aggregate` for collection.

## v0.0.2

- Update mock clasess to be treated as native motor's clasess.
- Add `create_indexes` and `index_information` to collection's async methods.

## v0.0.1

- Initial version with basic functionality loosely based on
    [this repository](https://github.com/gonzaloverussa/pytest-async-mongodb).
