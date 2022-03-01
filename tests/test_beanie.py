from typing import Optional
from beanie import Document, Link, WriteRules, Indexed, init_beanie
from pydantic import BaseModel
import pytest
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
    client = AsyncMongoMockClient('mongodb://user:pass@host:27017', connectTimeoutMS=250)

    await init_beanie(database=client.beanie_test, document_models=[Product])

    chocolate = Category(name='Chocolate', description='A preparation of roasted and ground cacao seeds.')
    tonybar = Product(name="Tony's", price=5.95, category=chocolate)
    await tonybar.insert()

    find_many = Product.find_many(Product.category == chocolate)
    assert find_many.motor_cursor
    assert await find_many.count() == 1

    product = await Product.find_one(Product.price < 10)
    await product.set({Product.name: 'Gold bar'})

    product = await Product.find_one(Product.category.name == 'Chocolade')
    assert product.name == 'Gold bar'
    assert product.category.description == chocolate.description


class Door(Document):
    height: int = 2
    width: int = 1


class House(Document):
    name: str
    door: Link[Door]


@pytest.mark.anyio
async def test_beanie_links():
    client = AsyncMongoMockClient('mongodb://user:pass@host:27017', connectTimeoutMS=250)

    await init_beanie(database=client.beanie_test, document_models=[Door, House])

    house = House(name='Nice House', door=Door(height=2.1))
    await house.insert(link_rule=WriteRules.WRITE)

    houses = await House.find(House.name == 'Nice House').to_list()
    assert len(houses) == 1
    house = houses[0]
    await house.fetch_all_links()
    assert house.door.height == 2
