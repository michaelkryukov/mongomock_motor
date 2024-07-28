from typing import Optional

import pytest
from beanie import Document, Indexed, Link, WriteRules, init_beanie
from pydantic import BaseModel

from mongomock_motor import AsyncMongoMockClient


class Category(BaseModel):
    name: str
    description: str


class Product(Document):
    name: str
    description: Optional[str] = None
    price: Indexed(float)
    category: Category


@pytest.mark.anyio
async def test_beanie():
    client = AsyncMongoMockClient(
        'mongodb://user:pass@host:27017', connectTimeoutMS=250
    )

    await init_beanie(database=client.beanie_test, document_models=[Product])

    chocolate = Category(
        name='Chocolate', description='A preparation of roasted and ground cacao seeds.'
    )

    tonybar = Product(name="Tony's", price=5.95, category=chocolate)
    await tonybar.insert()

    markbar = Product(name="Mark's", price=19.95, category=chocolate)
    await markbar.insert()

    find_many = Product.find_many(Product.category == chocolate, Product.price < 10)
    assert find_many.motor_cursor
    assert await find_many.count() == 1

    product = await Product.find_one(Product.price < 10)
    await product.set({Product.name: 'Gold bar'})

    product = await Product.find_one(Product.category.name == 'Chocolate')
    assert product.name == 'Gold bar'
    assert product.category.description == chocolate.description


class Door(Document):
    height: float = 2
    width: float = 1


class House(Document):
    name: str
    door: Link[Door]


@pytest.mark.anyio
async def test_beanie_links():
    client = AsyncMongoMockClient(
        'mongodb://user:pass@host:27017', connectTimeoutMS=250
    )

    await init_beanie(database=client.beanie_test, document_models=[Door, House])

    house = House(name='Nice House', door=Door(height=2.1))
    await house.insert(link_rule=WriteRules.WRITE)

    houses = await House.find(House.name == 'Nice House').to_list()
    assert len(houses) == 1
    house = houses[0]
    await house.fetch_all_links()
    assert house.door.height == 2.1


@pytest.mark.anyio
async def test_beanie_sort():
    client = AsyncMongoMockClient()
    await init_beanie(database=client.beanie_test, document_models=[Door])

    await Door.insert_many([Door(width=width) for width in [4, 2, 3, 1]])

    doors = await Door.find().sort(Door.width).to_list()
    assert [door.width for door in doors] == [1, 2, 3, 4]
