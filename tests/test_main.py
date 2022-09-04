import os

from main import app
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from httpx import AsyncClient
from sqlalchemy.orm import sessionmaker
from database import get_session, Base
import pytest
from models import Recipe, Ingredient

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)


async def get_session_overrides() -> AsyncSession:
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        yield session


app.dependency_overrides[get_session] = get_session_overrides


async def add_test_recipes():
    session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )()
    recipe1 = Recipe(id=1, dish_name="Test", cooking_time=7, description="Test",
                     ingredients=[Ingredient(name="Test")])
    recipe2 = Recipe(id=2, dish_name="Test2", cooking_time=9, description="Test2",
                     ingredients=[Ingredient(name="Test2")])
    session.add_all([recipe1, recipe2])
    await session.commit()
    return recipe1.id, recipe2.id


@pytest.fixture()
async def connection():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    recipe_id_1, recipe_id_2 = await add_test_recipes()

    yield recipe_id_1, recipe_id_2
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    os.remove('test.db')


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.mark.anyio
async def test_recipes_200(connection):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/recipes/"
        )
    assert response.status_code == 200


@pytest.mark.anyio
async def test_recipes_filling(connection):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/recipes/"
        )
    assert response.text
    answer = response.json()
    assert answer == [{'dish_name': 'Test', 'cooking_time': 7, 'id': 1, 'number_of_views': 0},
                      {'dish_name': 'Test2', 'cooking_time': 9, 'id': 2, 'number_of_views': 0}]


@pytest.mark.anyio
async def test_recipe_200(connection):
    recipe_id_1, recipe_id_2 = connection

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            f"/recipes/{recipe_id_1}"
        )
    assert response.status_code == 200


@pytest.mark.anyio
async def test_recipe_filling(connection):
    recipe_id_1, recipe_id_2 = connection

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            f"/recipes/{recipe_id_1}"
        )
    answer = response.json()
    assert answer == {'dish_name': 'Test', 'cooking_time': 7, 'description': 'Test', 'ingredient_list': ['Test']}


@pytest.mark.anyio
async def test_recipe_views(connection):
    recipe_id_1, recipe_id_2 = connection

    async with AsyncClient(app=app, base_url="http://test") as ac:
        await ac.get(
            f"/recipes/{recipe_id_1}"
        )
        response = await ac.get(
            "/recipes/"
        )
    answer = response.json()
    assert answer[0]['number_of_views'] == 1


@pytest.mark.anyio
async def test_recipe_rating(connection):
    recipe_id_1, recipe_id_2 = connection

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/recipes/"
        )
    answer = response.json()
    assert answer[0]['id'] == 1

    async with AsyncClient(app=app, base_url="http://test") as ac:
        await ac.get(
            f"/recipes/{recipe_id_2}"
        )
        response = await ac.get(
            "/recipes/"
        )
    answer = response.json()
    assert answer[0]['id'] == 2

    async with AsyncClient(app=app, base_url="http://test") as ac:
        await ac.get(
            f"/recipes/{recipe_id_1}"
        )
        response = await ac.get(
            "/recipes/"
        )
    answer = response.json()
    assert answer[0]['id'] == 1
