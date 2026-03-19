import datetime
import bcrypt
from pymongo import MongoClient
from bson.objectid import ObjectId
from app.models.user_model import User


class UserRepository:
    def __init__(self, uri: str, db_name: str):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.users = self.db["users"]

    def create_user(self, email: str, name: str, password: str) -> str:
        if self.users.find_one({"email": email}):
            raise ValueError("User with this email already exists")
        user = User(name=name, email=email, password=password)
        data = user.to_dict()
        data["date_of_join"] = datetime.datetime.utcnow().isoformat()
        result = self.users.insert_one(data)
        return str(result.inserted_id)

    def login_user(self, email: str, password: str):
        user = self.users.find_one({"email": email})
        if user and bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            return str(user["_id"])
        return None

    def get_user(self, uid: str):
        user = self.users.find_one({"_id": ObjectId(uid)})
        if user:
            user["_id"] = str(user["_id"])
            return user
        return None

    def update_user(self, uid: str, update_data: dict):
        self.users.update_one({"_id": ObjectId(uid)}, {"$set": update_data})
