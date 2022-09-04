from sqlalchemy import Column, String, Integer, ForeignKey, Table
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from database import Base

recipes_ingredients_table = Table(
    "recipes_ingredients",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id"), primary_key=True),
    Column("ingredient_id", ForeignKey("ingredients.id"), primary_key=True),
)


class Recipe(Base):
    """Recipe model description"""
    __tablename__ = 'recipes'
    id = Column(Integer, primary_key=True, index=True)
    dish_name = Column(String, index=True)
    number_of_views = Column(Integer, index=True, default=0)
    cooking_time = Column(Integer, index=True)
    description = Column(String, index=True)

    # ingredients = relationship("Ingredient", back_populates='recipe', cascade="all, delete-orphan")
    ingredients = relationship("Ingredient", secondary='recipes_ingredients', back_populates='recipes')

    @hybrid_property
    def ingredient_list(self) -> list:
        return [ing.name for ing in self.ingredients]


class Ingredient(Base):
    """Ingredient model description"""
    __tablename__ = 'ingredients'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    recipes = relationship("Recipe", secondary='recipes_ingredients', back_populates='ingredients')
