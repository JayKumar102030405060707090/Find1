from pymongo import MongoClient
from config import MONGO_URL

client = MongoClient(MONGO_URL)
db = client["find_partner"]
users = db["users"]

def find_match(current_user_id):
    current_user = users.find_one({"_id": current_user_id})
    if not current_user:
        return None

    gender = current_user.get("gender")
    age = current_user.get("age")

    if not gender or not age:
        return None

    # Find opposite gender user with similar age
    match = users.find_one({
        "_id": {"$ne": current_user_id},
        "gender": {"$ne": gender},
        "age": {"$gte": int(age) - 3, "$lte": int(age) + 3}
    })

    return match