from marshmallow.exceptions import ValidationError
from umongo import Document, fields
from umongo.instance import Instance
import pytest
from mongomock_motor import AsyncMongoMockClient


@pytest.mark.anyio
async def test_umongo():
    instance = Instance.from_db(AsyncMongoMockClient()['tests'])

    @instance.register
    class Something(Document):
        field1 = fields.StrField(required=True, unique=True)
        field2 = fields.StrField()
        related = fields.ListField(fields.ReferenceField('Something'))

        class Meta:
            collection_name = 'something'

    await Something.ensure_indexes()

    something1 = Something(field1='A', field2=':)', related=[])
    await something1.commit()

    with pytest.raises(ValidationError, match="^{'field1': 'Field value must be unique.'}$"):
        duplicate = Something(field1='A', field2=':)', related=[])
        await duplicate.commit()

    something2 = Something(field1='B', field2=';)', related=[something1])
    await something2.commit()

    found = await Something.find_one({'field1': 'B'})
    assert found
    assert found.field1 == 'B'
    assert found.field2 == ';)'
    assert len(found.related) == 1

    first_related = await found.related[0].fetch()
    assert first_related.field1 == 'A'
    assert first_related.field2 == ':)'
    assert first_related.related == []
