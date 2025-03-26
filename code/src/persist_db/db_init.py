import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pymongo.server_api import ServerApi

import os
load_dotenv()

def get_db():
    client = MongoClient(os.getenv("MONGO_DB_URI"), server_api=ServerApi('1'))
    db = client['email_classification_db']
    return db