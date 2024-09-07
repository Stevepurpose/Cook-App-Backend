from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from database import get_database
from sec import get_current_active_user , UserInDB # Import the authentication dependency

router = APIRouter()

def objectid_to_str(obj_id: ObjectId) -> str:
    return str(obj_id)

def str_to_objectid(obj_id: str) -> ObjectId:
    return ObjectId(obj_id)

@router.post("/recipes/", status_code=status.HTTP_201_CREATED, tags=["recipes"], summary="create an item")
async def create_recipe(recipe: dict, db: AsyncIOMotorClient = Depends(get_database), current_user: UserInDB = Depends(get_current_active_user)):
    recipe_data = recipe
    recipe_data['owner'] = current_user.username  # Associate the recipe with the current user
    result = await db["recipes"].insert_one(recipe_data)
    new_recipe = await db["recipes"].find_one({"_id": result.inserted_id})
    if new_recipe:
        new_recipe["id"] = objectid_to_str(new_recipe["_id"])
        del new_recipe["_id"]
        return new_recipe
    raise HTTPException(status_code=400, detail="Failed to create recipe")

@router.get("/recipes/{recipe_id}", tags=["recipes"], summary="get a specified item")
async def get_recipe(recipe_id: str, db: AsyncIOMotorClient = Depends(get_database)):
    obj_id = str_to_objectid(recipe_id)
    recipe = await db["recipes"].find_one({"_id": obj_id})
    if recipe:
        recipe["id"] = objectid_to_str(recipe["_id"])
        del recipe["_id"]  # Remove the original _id field from the response
        return recipe
    raise HTTPException(status_code=404, detail="Recipe not found")

@router.put("/recipes/{recipe_id}", tags=["recipes"], summary="only send changed fields")
async def update_recipe(recipe_id: str, recipe_update: dict, db: AsyncIOMotorClient = Depends(get_database), current_user: dict = Depends(get_current_active_user)):
    obj_id = str_to_objectid(recipe_id)
    update_result = await db["recipes"].update_one(
        {"_id": obj_id},  # Filter to match the recipe by its ObjectId
        {"$set": recipe_update}  # Use $set to update fields
    )
    
    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Fetch the updated recipe
    updated_recipe = await db["recipes"].find_one({"_id": obj_id})
    
    if updated_recipe:
        updated_recipe["id"] = objectid_to_str(updated_recipe["_id"])
        del updated_recipe["_id"]  # Remove the original _id field from the response
        return updated_recipe
    else:
        raise HTTPException(status_code=404, detail="Recipe not found")

@router.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["recipes"], summary="delete specified recipe")
async def delete_recipe(recipe_id: str, db: AsyncIOMotorClient = Depends(get_database), current_user: dict = Depends(get_current_active_user)):
    obj_id = str_to_objectid(recipe_id)
    deleted_recipe = await db["recipes"].find_one_and_delete({"_id": obj_id})
    
    if not deleted_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

@router.get("/recipes/", tags=["recipes"], summary="get all recipes")
async def get_all_recipes(db: AsyncIOMotorClient = Depends(get_database)):
    recipes = await db["recipes"].find().to_list(1000)
    for recipe in recipes:
        recipe["id"] = objectid_to_str(recipe["_id"])
        del recipe["_id"]  # Remove the original _id field from each recipe
    return recipes
