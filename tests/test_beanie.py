from typing import Optional
from beanie import Document, Indexed, init_beanie
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
