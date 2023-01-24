import pymongo
import settings

MONGODB_USER = settings.mongodb_user
MONGODB_PASSWORD = settings.mongodb_password
MONGODB_CLUSTER = settings.mongodb_cluster

MONGODB_URI = f"mongodb+srv://{MONGODB_USER}:{MONGODB_PASSWORD}@cluster0.{MONGODB_CLUSTER}.mongodb.net/?retryWrites=true&w=majority"
myclient = pymongo.MongoClient(MONGODB_URI)
mydb = myclient["tasks_db"]
product = mydb["products"]
price = mydb["productPriceHistory"]

x = product.delete_many({})
y = price.delete_many({})

print(x.deleted_count, "documents deleted")
print(y.deleted_count, "documents deleted")
