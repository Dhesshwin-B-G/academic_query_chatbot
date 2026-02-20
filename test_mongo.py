from pymongo import MongoClient

uri = "mongodb+srv://dhesshwin19_db_user:Z1en8vaqKvTckqoj@cluster-1.tsbcjyq.mongodb.net/?appName=Cluster-1"

client = MongoClient(uri)
print(client.list_database_names())
