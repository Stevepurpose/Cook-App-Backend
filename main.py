from fastapi import FastAPI, Depends, status, HTTPException, APIRouter
from database import startup_db_client, shutdown_db_client, get_database
from routes import recipe
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing_extensions import Annotated
from jwt.exceptions import InvalidTokenError
from sec import create_user, UserIn, UserInDB, UserOut, Token, authenticate_user, create_access_token, get_current_active_user
from bson import ObjectId

app = FastAPI()
load_dotenv()

origins = [
    "http://localhost:3000",
    "https://thecookapp.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

mongo_uri = os.getenv("CONN_STR")

client = AsyncIOMotorClient(mongo_uri)
db = client["Kitchen"]


class SupportMessage(BaseModel):
    message: str


def objectid_to_str(obj_id: ObjectId) -> str:
    return str(obj_id)

def str_to_objectid(obj_id: str) -> ObjectId:
    return ObjectId(obj_id)


@app.post("/support")
async def receive_support_message(support_message: SupportMessage):
    message_data = support_message.dict()
    # Save the message to the support_messages collection
    await db["support_messages"].insert_one(message_data)
    return {"detail": "Message received"}


@app.post("/user/")
async def create_user_endpoint(user_in: UserIn):
    return await create_user(user_in)


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    return current_user


@app.get("/users/me/items", tags=["users"], summary="Get recipes created by the current user")
async def read_own_items(current_user: UserInDB = Depends(get_current_active_user), db: AsyncIOMotorClient = Depends(get_database)):
    user_recipes = await db["recipes"].find({"owner": current_user.username}).to_list(100)  # Find recipes created by the current user
    for recipe in user_recipes:
        recipe["id"] = objectid_to_str(recipe["_id"])
        del recipe["_id"]
    return user_recipes



@app.on_event("startup")
async def on_startup():
    await startup_db_client(app)  # Pass the app instance to setup the MongoDB client

@app.on_event("shutdown")
async def on_shutdown():
    await shutdown_db_client(app)

# Include the recipe router
app.include_router(recipe.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


