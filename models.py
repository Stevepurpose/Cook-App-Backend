from pydantic import BaseModel, Field
from typing import List, Union



class Recipe(BaseModel):
    food_name: str
    origin: str
    eaten_with: str
    as_appetizer: bool
    as_main: bool
    as_dessert: bool
    ingredients: str
    directions: str
    nutritional_benefits: str
    chef: str
    contact:Union[str, None] = None

    class Config:
        orm_mode = True


class RecipeUpdate(BaseModel):
    food_name: Union[str, None] = None
    origin: Union[str, None] = None
    eaten_with: Union[str, None] = None
    as_appetizer: Union[bool, None] = None
    as_main: Union[bool, None] = None
    as_dessert: Union[bool, None] = None
    ingredients: Union[str, None] = None
    directions: Union[str, None] = None
    nutritional_benefits: Union[str, None] = None
    chef: Union[str, None] = None
    contact: Union[str, None] = None

