from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import List, Dict, Any
from textblob import TextBlob
import time

class RecipeApp:
    def __init__(self):
        # Add a small delay before connecting to MongoDB
        time.sleep(1)
        try:
            self.client = MongoClient('mongodb://mymongo:27017/', serverSelectionTimeoutMS=5000)
            # Test the connection
            self.client.server_info()
            self.db = self.client['RecipeHub']
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def close(self):
        if hasattr(self, 'client'):
            self.client.close()
            
        #base function to return important information about a recipe
    def search_recipes(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        return list(self.db.recipes.find(
            {"$text": {"$search": query}},
            {
                "name": 1,
                "ingredients": 1,
                "avg_rating": 1,
                "original_id": 1,
                "_id": 1  # Explicitly include the _id field
            }
        ).limit(limit))

#finding recipes by cooktime. We are limiting the responses to 5 so things dont get too crazy
#searching my lte since we want our time and anything less. We sort to show the
    def find_by_cooking_time(self, minutes: int, limit: int = 5) -> List[Dict[str, Any]]:
        return list(self.db.recipes.find(
            {"minutes": {"$lte": minutes}},
            {
                "name": 1,
                "minutes": 1,
                "avg_rating": 1,
                "_id": 1,
                "original_id": 1,
                "ingredients": 1  # Including ingredients for better context
            }
        ).sort([
            ("minutes", -1),  # Sort by minutes in descending order
            ("avg_rating", -1)  # Then by rating in descending order
        ]).limit(limit))
#allows for searching a specific nutrion amount in the
    def find_by_nutrition(self, nutrient: str, max_value: float, limit: int = 5) -> List[Dict[str, Any]]:
        query_field = f"nutrition.{nutrient}"
        return list(self.db.recipes.find(
            {query_field: {"$lte": max_value}},
            {"name": 1, "nutrition": 1, "avg_rating": 1}
        ).sort("avg_rating", -1).limit(limit))

    def find_by_cuisine(self, cuisine: str, limit: int = 5) -> List[Dict[str, Any]]:
        return list(self.db.recipes.find(
            {"tags": {"$regex": cuisine, "$options": "i"}},
            {"name": 1, "tags": 1, "avg_rating": 1, "ingredients": 1}
        ).sort("avg_rating", -1).limit(limit))

    def find_similar_recipes(self, recipe_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            original_id = int(recipe_id)  # Convert string input to integer
            recipe = self.db.recipes.find_one({"original_id": original_id})
            if not recipe:
                return []

            return list(self.db.recipes.aggregate([
                {
                    "$match": {
                        "original_id": {"$ne": original_id},
                        "ingredients": {"$in": recipe["ingredients"]}
                    }
                },
                {
                    "$addFields": {
                        "common_ingredients": {
                            "$size": {
                                "$setIntersection": ["$ingredients", recipe["ingredients"]]
                            }
                        }
                    }
                },
                {"$sort": {"common_ingredients": -1, "avg_rating": -1}},
                {"$limit": limit},
                {
                    "$project": {
                        "original_id": 1,
                        "name": 1,
                        "ingredients": 1,
                        "avg_rating": 1,
                        "common_ingredients": 1
                    }
                }
            ]))
        except ValueError:
            print("Error: Recipe ID must be a number")
            return []
    def find_top_rated(self, limit: int = 5) -> List[Dict[str, Any]]:
        return list(self.db.recipes.find(
            {"review_count": {"$gte": 10}},  # Only include recipes with at least 10 reviews
            {
                "name": 1,
                "ingredients": 1,
                "tags": 1,
                "avg_rating": 1,
                "review_count": 1
            }
        ).sort([
            ("avg_rating", -1),
            ("review_count", -1)
        ]).limit(limit))

    def get_personalized_recommendations(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        # Convert user_id to integer if it's numeric
        try:
            # Convert user_id to integer
            numeric_user_id = int(user_id)

            # First, efficiently get user's rated recipes with index
            user_ratings = list(self.db.reviews.find(
                {"user_id": numeric_user_id},
                {"recipe_id": 1, "rating": 1, "_id": 0}
            ).hint("user_id_1"))  # Use the existing index

            if not user_ratings:
                print(f"No rating history found for user {user_id}. Showing top-rated recipes instead.")
                return list(self.db.recipes.find(
                    {"avg_rating": {"$exists": True, "$gte": 4.0}, "review_count": {"$gte": 10}},
                    {"name": 1, "ingredients": 1, "tags": 1, "avg_rating": 1}
                ).sort("avg_rating", -1).limit(limit))

            # Get highly rated recipes (4 or 5 stars)
            liked_recipe_ids = [r["recipe_id"] for r in user_ratings if r["rating"] >= 4]

            if not liked_recipe_ids:
                print(f"No highly rated recipes found for user {user_id}. Showing top-rated recipes instead.")
                return list(self.db.recipes.find(
                    {"avg_rating": {"$exists": True, "$gte": 4.0}, "review_count": {"$gte": 10}},
                    {"name": 1, "ingredients": 1, "tags": 1, "avg_rating": 1}
                ).sort("avg_rating", -1).limit(limit))

            # Get liked recipes' ingredients and tags efficiently
            liked_recipes = list(self.db.recipes.find(
                {"_id": {"$in": liked_recipe_ids}},
                {"ingredients": 1, "tags": 1}
            ))

            # Extract unique ingredients and tags
            liked_ingredients = set()
            liked_tags = set()
            for recipe in liked_recipes:
                liked_ingredients.update(recipe.get("ingredients", []))
                liked_tags.update(recipe.get("tags", []))

            # Convert to lists for MongoDB query
            ingredients_list = list(liked_ingredients)[:50]  # Limit to top 50 ingredients
            tags_list = list(liked_tags)[:20]  # Limit to top 20 tags

            # Get recipes the user hasn't rated
            rated_recipe_ids = [r["recipe_id"] for r in user_ratings]

            # Simplified and optimized aggregation pipeline
            pipeline = [
                {
                    "$match": {
                        "_id": {"$nin": rated_recipe_ids},
                        "$or": [
                            {"ingredients": {"$in": ingredients_list}},
                            {"tags": {"$in": tags_list}}
                        ],
                        "avg_rating": {"$gte": 3.5}  # Only consider well-rated recipes
                    }
                },
                {
                    "$addFields": {
                        "ingredient_match": {
                            "$size": {
                                "$setIntersection": ["$ingredients", ingredients_list]
                            }
                        },
                        "tag_match": {
                            "$size": {
                                "$setIntersection": ["$tags", tags_list]
                            }
                        }
                    }
                },
                {
                    "$addFields": {
                        "match_score": {
                            "$add": [
                                "$ingredient_match",
                                {"$multiply": ["$tag_match", 2]},
                                {"$multiply": [{"$ifNull": ["$avg_rating", 3.5]}, 2]}
                            ]
                        }
                    }
                },
                {"$sort": {"match_score": -1}},
                {"$limit": limit},
                {
                    "$project": {
                        "name": 1,
                        "ingredients": 1,
                        "tags": 1,
                        "avg_rating": 1,
                        "match_score": 1
                    }
                }
            ]

            # Execute aggregation with timeout
            recommendations = list(self.db.recipes.aggregate(
                pipeline,
                maxTimeMS=5000  # 5-second timeout
            ))

            return recommendations

        except Exception as e:
            print(f"Error generating recommendations: {str(e)}")
            # Fallback to top-rated recipes
            return list(self.db.recipes.find(
                {"avg_rating": {"$exists": True, "$gte": 4.0}, "review_count": {"$gte": 10}},
                {"name": 1, "ingredients": 1, "tags": 1, "avg_rating": 1}
            ).sort("avg_rating", -1).limit(limit))

    def analyze_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze recipe trends and seasonal patterns with improved formatting"""
        cutoff_date = datetime.now() - timedelta(days=days)

        # Analyze trending recipes
        trending = list(self.db.reviews.aggregate([
            {"$match": {"date": {"$gte": cutoff_date}}},
            {
                "$group": {
                    "_id": "$recipe_id",
                    "recent_ratings": {"$avg": "$rating"},
                    "review_count": {"$sum": 1}
                }
            },
            {"$match": {"review_count": {"$gte": 5}}},
            {"$sort": {"recent_ratings": -1, "review_count": -1}},
            {"$limit": 10},
            {
                "$lookup": {
                    "from": "recipes",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "recipe"
                }
            },
            {"$unwind": "$recipe"},
            {
                "$project": {
                    "name": "$recipe.name",
                    "recent_ratings": 1,
                    "review_count": 1,
                    "tags": "$recipe.tags"
                }
            }
        ]))

        # Analyze seasonal patterns
        seasonal = list(self.db.reviews.aggregate([
            {
                "$group": {
                    "_id": {
                        "recipe": "$recipe_id",
                        "month": {"$month": "$date"}
                    },
                    "avg_rating": {"$avg": "$rating"},
                    "count": {"$sum": 1}
                }
            },
            {"$match": {"count": {"$gte": 5}}},
            {"$sort": {"avg_rating": -1}},
            {
                "$lookup": {
                    "from": "recipes",
                    "localField": "_id.recipe",
                    "foreignField": "_id",
                    "as": "recipe"
                }
            },
            {"$unwind": "$recipe"},
            {
                "$project": {
                    "name": "$recipe.name",
                    "month": "$_id.month",
                    "avg_rating": 1,
                    "count": 1,
                    "tags": "$recipe.tags"
                }
            }
        ]))

        # Organize seasonal data by month
        months = {1: 'January', 2: 'February', 3: 'March', 4: 'April',
                 5: 'May', 6: 'June', 7: 'July', 8: 'August',
                 9: 'September', 10: 'October', 11: 'November', 12: 'December'}

        seasonal_by_month = {}
        for month_num in range(1, 13):
            month_name = months[month_num]
            month_recipes = [r for r in seasonal if r['month'] == month_num]
            if month_recipes:
                seasonal_by_month[month_name] = {
                    'top_recipes': sorted(month_recipes,
                                       key=lambda x: (-x['avg_rating'], -x['count']))[:5],
                    'recipe_count': len(month_recipes),
                    'avg_rating': sum(r['avg_rating'] for r in month_recipes) / len(month_recipes)
                }

        return {
            "trending_recipes": [{
                "name": recipe["name"],
                "rating": round(recipe["recent_ratings"], 2),
                "reviews": recipe["review_count"],
                "tags": recipe["tags"][:3] if recipe.get("tags") else []  # Show only top 3 tags
            } for recipe in trending],
            "seasonal_patterns": {
                month: {
                    "stats": {
                        "average_rating": round(data["avg_rating"], 2),
                        "total_recipes": data["recipe_count"]
                    },
                    "top_recipes": [{
                        "name": recipe["name"],
                        "rating": round(recipe["avg_rating"], 2),
                        "reviews": recipe["count"]
                    } for recipe in data["top_recipes"][:5]]  # Limit to top 5 recipes
                } for month, data in seasonal_by_month.items()
            }
        }

    def analyze_sentiment_detailed(self, recipe_name: str) -> Dict[str, Any]:
        recipe = self.db.recipes.find_one({"name": {"$regex": recipe_name, "$options": "i"}})
        if not recipe:
            return None

        reviews = list(self.db.reviews.find({"recipe_id": recipe["_id"]}))
        sentiment_scores = []

        for review in reviews:
            if review.get("review"):
                analysis = TextBlob(review["review"])
                sentiment_scores.append({
                    "polarity": analysis.sentiment.polarity,
                    "subjectivity": analysis.sentiment.subjectivity,
                    "rating": review["rating"],
                    "review": review["review"]
                })

        if not sentiment_scores:
            return None

        avg_sentiment = sum(s["polarity"] for s in sentiment_scores) / len(sentiment_scores)
        avg_subjectivity = sum(s["subjectivity"] for s in sentiment_scores) / len(sentiment_scores)

        return {
            "recipe_name": recipe["name"],
            "avg_rating": recipe.get("avg_rating", 0),
            "review_count": len(reviews),
            "avg_sentiment": avg_sentiment,
            "avg_subjectivity": avg_subjectivity,
            "sentiment_distribution": {
                "positive": len([s for s in sentiment_scores if s["polarity"] > 0]),
                "neutral": len([s for s in sentiment_scores if s["polarity"] == 0]),
                "negative": len([s for s in sentiment_scores if s["polarity"] < 0])
            },
            "sample_reviews": sorted(sentiment_scores, key=lambda x: abs(x["polarity"]), reverse=True)[:5]
        }
    def find_by_diet(self, restriction: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find recipes that match dietary restrictions"""
        restriction = restriction.lower()
        diet_keywords = {
            'vegetarian': ['vegetarian', '-chicken', '-beef', '-pork', '-fish'],
            'vegan': ['vegan', '-meat', '-egg', '-dairy', '-cheese'],
            'gluten-free': ['gluten-free', '-wheat', '-flour'],
            'keto': ['keto', 'low-carb'],
            'paleo': ['paleo', '-grain', '-dairy'],
            'dairy-free': ['dairy-free', '-milk', '-cheese', '-cream']
        }

        if restriction not in diet_keywords:
            return []

        query = {"$and": []}

        # Add positive keywords
        positive_terms = [kw for kw in diet_keywords[restriction] if not kw.startswith('-')]
        if positive_terms:
            query["$and"].append({"tags": {"$in": positive_terms}})

        # Add negative keywords
        negative_terms = [kw[1:] for kw in diet_keywords[restriction] if kw.startswith('-')]
        if negative_terms:
            for term in negative_terms:
                query["$and"].append({
                    "$and": [
                        {"ingredients": {"$not": {"$regex": term, "$options": "i"}}},
                        {"tags": {"$not": {"$regex": term, "$options": "i"}}}
                    ]
                })

        return list(self.db.recipes.find(
            query,
            {"name": 1, "ingredients": 1, "tags": 1, "avg_rating": 1, "nutrition": 1}
        ).sort("avg_rating", -1).limit(limit))

    def analyze_nutritional_patterns(self, user_id: str = None) -> Dict[str, Any]:
        match_stage = {}
        if user_id:
            try:
                # Convert string user_id to integer for database matching
                user_id_int = int(user_id)
                print(f"\nLooking up reviews for user {user_id_int}...")

                # Find all reviews for this user
                user_reviews = list(self.db.reviews.find({"user_id": user_id_int}))
                print(f"Found {len(user_reviews)} reviews")

                if not user_reviews:
                    print("No reviews found for this user.")
                    return {
                        "overall_stats": None,
                        "calorie_distribution": {},
                        "sample_recipes": {"low_calorie": [], "high_protein": []}
                    }

                # Get recipe IDs from reviews
                rated_recipes = [r["recipe_id"] for r in user_reviews]
                print(f"User has rated {len(rated_recipes)} recipes")

                # Verify recipes exist
                recipes_found = self.db.recipes.count_documents({"_id": {"$in": rated_recipes}})
                print(f"Found {recipes_found} matching recipes in database")

                match_stage = {"_id": {"$in": rated_recipes}}

            except ValueError:
                print(f"Error: Invalid user ID format '{user_id}'. Must be a number.")
                return {
                    "overall_stats": None,
                    "calorie_distribution": {},
                    "sample_recipes": {"low_calorie": [], "high_protein": []}
                }

        # Calculate nutrition statistics
        print("\nCalculating nutrition statistics...")
        nutrition_stats = list(self.db.recipes.aggregate([
            {"$match": match_stage},
            {
                "$match": {
                    "nutrition": {"$exists": True},
                    "nutrition.calories": {"$exists": True}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_calories": {"$avg": "$nutrition.calories"},
                    "avg_protein": {"$avg": "$nutrition.protein"},
                    "avg_fat": {"$avg": "$nutrition.total_fat"},
                    "avg_carbs": {"$avg": "$nutrition.carbohydrates"},
                    "recipe_count": {"$sum": 1}
                }
            }
        ]))

        if not nutrition_stats:
            print("No recipes with nutrition data found.")
            return {
                "overall_stats": None,
                "calorie_distribution": {},
                "sample_recipes": {"low_calorie": [], "high_protein": []}
            }

        print(f"Found nutrition data for {nutrition_stats[0]['recipe_count']} recipes")

        # Calculate calorie distribution
        print("\nCalculating calorie distribution...")
        distribution = list(self.db.recipes.aggregate([
            {"$match": match_stage},
            {
                "$match": {
                    "nutrition.calories": {"$exists": True}
                }
            },
            {
                "$bucket": {
                    "groupBy": "$nutrition.calories",
                    "boundaries": [0, 300, 600, 1000, 2000],
                    "default": "2000+",
                    "output": {
                        "count": {"$sum": 1},
                        "avg_rating": {"$avg": "$avg_rating"}
                    }
                }
            }
        ]))

        # Get sample recipes
        print("\nFetching sample recipes...")
        low_cal_samples = list(self.db.recipes.find(
            {
                **match_stage,
                "nutrition.calories": {"$lte": 300},
                "nutrition.calories": {"$exists": True}
            },
            {
                "name": 1,
                "nutrition": 1,
                "avg_rating": 1
            }
        ).sort("avg_rating", -1).limit(3))

        high_protein_samples = list(self.db.recipes.find(
            {
                **match_stage,
                "nutrition.protein": {"$gte": 20},
                "nutrition.protein": {"$exists": True}
            },
            {
                "name": 1,
                "nutrition": 1,
                "avg_rating": 1
            }
        ).sort("avg_rating", -1).limit(3))

        print(f"Found {len(low_cal_samples)} low calorie and {len(high_protein_samples)} high protein samples")

        # Format calorie distribution for output
        calorie_ranges = {
            "0-300": "Low Calorie",
            "300-600": "Medium Calorie",
            "600-1000": "High Calorie",
            "1000-2000": "Very High Calorie",
            "2000+": "Extremely High Calorie"
        }

        formatted_distribution = {}
        for bucket in distribution:
            range_key = f"{bucket['_id']}" if isinstance(bucket['_id'], str) else f"{bucket['_id']}-{bucket['_id'] + 300}"
            formatted_distribution[calorie_ranges.get(range_key, range_key)] = {
                "count": bucket["count"],
                "avg_rating": round(bucket["avg_rating"], 2) if "avg_rating" in bucket else None
            }

        return {
            "overall_stats": nutrition_stats[0] if nutrition_stats else None,
            "calorie_distribution": formatted_distribution,
            "sample_recipes": {
                "low_calorie": low_cal_samples,
                "high_protein": high_protein_samples
            }
        }
