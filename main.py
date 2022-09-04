from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

import uvicorn
from fastapi import FastAPI
from sqlalchemy.orm import selectinload
from models import Recipe, Ingredient
from fastapi import Depends
from sqlalchemy.future import select
from schemas import RecipeMain, RecipeDetails
from database import get_session, engine, Base
from sqlalchemy.orm import sessionmaker

app = FastAPI()


async def fill_db(eng):
    session = sessionmaker(
        eng, expire_on_commit=False, class_=AsyncSession
    )()
    res = await session.execute(select(Recipe))
    if res.first():
        return
    cucumber = Ingredient(name="Огурец")
    tomato = Ingredient(name="Помидор")
    salt = Ingredient(name="Соль")
    pelmeni = Ingredient(name="Пельмени")
    butter = Ingredient(name="Сливочное масло")
    cereals = Ingredient(name="Овсяные хлопья")
    milk = Ingredient(name="Молоко")
    session.add_all(
        [
            Recipe(id=1, dish_name="Салат с огурцом и помидором", cooking_time=7,
                   description="Огурец, помидор, лук помыть и порезать средними кусками. Добавить майонез, "
                               "соль, перемешать.",
                   ingredients=[cucumber, tomato, salt]),
            Recipe(id=2, dish_name="Жареные пельмени", cooking_time=15,
                   description="Замороженные пельмени выложить на сковороду, смазанную сливочным маслом. Жарить "
                               "15 минут с обеих сторон на среднем огне.",
                   ingredients=[pelmeni, butter]),
            Recipe(id=3, dish_name="Каша овсяная", cooking_time=25,
                   description="В кастрюлю положить овсянку с молоком в соотношении 1:3, варить 20 мин на слабом "
                               "огне. Выключить огонь, дать постоять 5 минут под крышкой. Добавить кусок масла.",
                   ingredients=[cereals, milk, butter]),
        ]
    )
    await session.commit()


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await fill_db(engine)


@app.get('/recipes/', response_model=List[RecipeMain], tags=["Recipes"], summary="Return list of recipes")
async def recipes(session: AsyncSession = Depends(get_session)) -> List[Recipe]:
    """Возвращает список доступных рецептов. Отсортированы по числу просмотров и времени готовки."""
    res = await session.execute(select(Recipe).order_by(
        Recipe.number_of_views.desc(),
        Recipe.cooking_time
    ))
    return res.scalars().all()


@app.get('/recipes/{id}', response_model=RecipeDetails, tags=["Recipes"], summary="Return one recipe")
async def recipes(id: int, session: AsyncSession = Depends(get_session)) -> Recipe:
    """Возвращает рецепт с описанием деталей."""
    execution = await session.execute(select(Recipe).filter(
        Recipe.id == id
    ).options(
        selectinload(Recipe.ingredients)
    ))
    recipe = execution.scalars().first()
    recipe.number_of_views += 1
    await session.commit()
    return recipe


if __name__ == '__main__':
    uvicorn.run('main:app', port=5000, host='127.0.0.1', reload=True)
