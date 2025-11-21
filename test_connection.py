from pymongo import MongoClient

print("Starting connection test...", flush=True)

client = MongoClient('mongodb://mymongo:27017/')
db = client['RecipeHub']

recipe_count = db.recipes.count_documents({})
print(f"Found {recipe_count} recipes in the database", flush=True)

client.close()
print("Test completed!", flush=True)
