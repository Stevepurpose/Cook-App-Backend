import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from fastapi import FastAPI
from typing import AsyncGenerator

# Load environment variables from .env file
load_dotenv()

class Settings:
    def __init__(self):
        # Load the MongoDB URI from the environment variable
        self.mongo_uri = os.getenv("CONN_STR")
        self.mongo_db = "Kitchen"

settings = Settings()

async def ping_server() -> AsyncIOMotorClient:
    client = AsyncIOMotorClient(settings.mongo_uri, server_api=ServerApi('1'))
    try:
        await client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        return client
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise

async def startup_db_client(app: FastAPI) -> None:
    app.mongodb_client = await ping_server()
    app.mongodb = app.mongodb_client[settings.mongo_db]

async def shutdown_db_client(app: FastAPI) -> None:
    app.mongodb_client.close()

# Dependency to get the database client
async def get_database() -> AsyncGenerator:
    client = await ping_server()
    try:
        yield client[settings.mongo_db]
    finally:
        client.close()
