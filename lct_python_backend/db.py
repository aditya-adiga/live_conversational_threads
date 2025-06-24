from databases import Database
import os

DATABASE_URL = os.getenv("DATABASE_URL")

db = Database(DATABASE_URL)