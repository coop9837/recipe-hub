import os
import json
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from tqdm import tqdm
import ast
import kagglehub

def connect_to_mongodb():
    client = MongoClient('mongodb://mymongo:27017/')
    db = client['RecipeHub']
    return client, db

def process_nutrition(nutrition_str):
    """Convert nutrition list to structured dictionary"""
    try:
        if isinstance(nutrition_str, str):
            nutrition_list = ast.literal_eval(nutrition_str)
        else:
            nutrition_list = nutrition_str

        return {
            "calories": nutrition_list[0],
            "total_fat": nutrition_list[1],
            "sugar": nutrition_list[2],
            "sodium": nutrition_list[3],
            "protein": nutrition_list[4],
            "saturated_fat": nutrition_list[5],
            "carbohydrates": nutrition_list[6]
        }
    except:
        return {}

def import_shuyangli_dataset(path, db):
    """Import data from shuyangli94 dataset"""
    recipes_df = pd.read_csv(f"{path}/RAW_recipes.csv")
    interactions_df = pd.read_csv(f"{path}/RAW_interactions.csv")
    recipe_id_mapping = {}

    print("Processing shuyangli94 recipes...")
    for _, row in tqdm(recipes_df.iterrows(), total=len(recipes_df)):
        try:
            recipe_doc = {
                "original_id": row['id'],
                "name": row['name'],
                "ingredients": ast.literal_eval(row['ingredients']),
                "steps": ast.literal_eval(row['steps']),
                "minutes": row['minutes'],
                "tags": ast.literal_eval(row['tags']),
                "nutrition": process_nutrition(row['nutrition']),
                "source_dataset": "shuyangli94",
                "n_steps": row['n_steps'],
                "n_ingredients": row['n_ingredients'],
                "reviews": []
            }

            result = db.recipes.insert_one(recipe_doc)
            recipe_id_mapping[row['id']] = result.inserted_id
        except Exception as e:
            print(f"Error processing recipe {row['id']}: {e}")
            continue

    print("Processing shuyangli94 interactions...")
    for _, row in tqdm(interactions_df.iterrows(), total=len(interactions_df)):
        try:
            if row['recipe_id'] in recipe_id_mapping:
                review_doc = {
                    "recipe_id": recipe_id_mapping[row['recipe_id']],
                    "user_id": row['user_id'],
                    "date": datetime.strptime(row['date'], '%Y-%m-%d'),
                    "rating": row['rating'],
                    "review": row['review'],
                    "source_dataset": "shuyangli94"
                }
                db.reviews.insert_one(review_doc)

                db.recipes.update_one(
                    {"_id": recipe_id_mapping[row['recipe_id']]},
                    {"$push": {"reviews": {
                        "rating": row['rating'],
                        "date": datetime.strptime(row['date'], '%Y-%m-%d'),
                        "summary": row['review'][:100] if pd.notna(row['review']) else None
                    }}}
                )
        except Exception as e:
            print(f"Error processing review for recipe {row['recipe_id']}: {e}")
            continue

def create_indexes(db):
    """Create indexes for better query performance"""
    print("Creating indexes...")

    # Existing indexes
    db.recipes.create_index([("name", "text"), ("ingredients", "text")])
    db.recipes.create_index("source_dataset")
    db.recipes.create_index("tags")
    db.recipes.create_index("minutes")
    db.recipes.create_index("n_ingredients")
    db.recipes.create_index([("nutrition.calories", 1)])

    db.reviews.create_index("recipe_id")
    db.reviews.create_index("user_id")
    db.reviews.create_index("date")
    db.reviews.create_index("rating")
    db.reviews.create_index("source_dataset")

    # New indexes for recommendations
    db.recipes.create_index([("avg_rating", -1)])
    db.recipes.create_index([("ingredients", 1)])

    print("Indexes created successfully!")

def calculate_recipe_stats(db):
    """Calculate and update recipe statistics"""
    print("Calculating recipe statistics...")

    pipeline = [
        {
            "$group": {
                "_id": "$recipe_id",
                "avg_rating": {"$avg": "$rating"},
                "review_count": {"$sum": 1},
                "ratings_distribution": {
                    "$push": "$rating"
                }
            }
        }
    ]

    recipe_stats = db.reviews.aggregate(pipeline)

    for stat in recipe_stats:
        try:
            # Convert integer keys to strings
            ratings_dist = {str(i): stat['ratings_distribution'].count(i)
                          for i in range(1, 6)}

            db.recipes.update_one(
                {"_id": stat['_id']},
                {"$set": {
                    "avg_rating": stat['avg_rating'],
                    "review_count": stat['review_count'],
                    "ratings_distribution": ratings_dist
                }}
            )
        except Exception as e:
            print(f"Error calculating stats for recipe {stat['_id']}: {e}")
            continue
def analyze_dataset_coverage(db):
    """Analyze and print statistics about dataset coverage"""
    print("\nDataset Coverage Analysis:")

    total_recipes = db.recipes.count_documents({})
    total_reviews = db.reviews.count_documents({})

    print(f"Total recipes: {total_recipes}")
    print(f"Total reviews: {total_reviews}")

if __name__ == "__main__":
    try:
        client, db = connect_to_mongodb()
        db.recipes.drop()
        db.reviews.drop()

        shuyangli_path = kagglehub.dataset_download(
            "shuyangli94/food-com-recipes-and-user-interactions"
        )
        import_shuyangli_dataset(shuyangli_path, db)
        create_indexes(db)
        calculate_recipe_stats(db)
        analyze_dataset_coverage(db)

        print("Data import and processing completed successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()
