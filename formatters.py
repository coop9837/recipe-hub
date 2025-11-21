from typing import Dict, Any, List

def format_trend_output(trend_data: Dict[str, Any]) -> None:
    """Format and print trend analysis results with improved readability"""

    # Print Trending Recipes section
    print("\n=== TRENDING RECIPES ===")
    print("-" * 50)
    for i, recipe in enumerate(trend_data["trending_recipes"], 1):
        print(f"\n{i}. {recipe['name']}")
        print(f"   Rating: {recipe['rating']:.1f} ★ ({recipe['reviews']} reviews)")
        if recipe.get('tags'):
            print(f"   Tags: {', '.join(recipe['tags'])}")

    # Print Seasonal Patterns section
    print("\n\n=== SEASONAL PATTERNS ===")
    print("-" * 50)

    for month, data in trend_data["seasonal_patterns"].items():
        print(f"\n{month}")
        print(f"Average Rating: {data['stats']['average_rating']:.1f} ★")
        print(f"Total Recipes: {data['stats']['total_recipes']}")

        if data['top_recipes']:
            print("\nTop Recipes:")
            for i, recipe in enumerate(data['top_recipes'], 1):
                print(f"{i}. {recipe['name']}")
                print(f"   Rating: {recipe['rating']:.1f} ★ ({recipe['reviews']} reviews)")

def format_nutrition_analysis(nutrition_data: Dict[str, Any]) -> None:
    """Format and print nutritional analysis results"""
    if not nutrition_data["overall_stats"]:
        print("\nNo nutritional data available")
        return

    stats = nutrition_data["overall_stats"]
    print("\nOverall Nutritional Statistics:")
    print(f"Average Calories: {stats['avg_calories']:.1f}")
    print(f"Average Protein: {stats['avg_protein']:.1f}g")
    print(f"Average Fat: {stats['avg_fat']:.1f}g")
    print(f"Average Carbs: {stats['avg_carbs']:.1f}g")

    print("\nCalorie Distribution:")
    for category, count in nutrition_data["calorie_distribution"].items():
        print(f"{category}: {count} recipes")

    print("\nSample Low-Calorie Recipes:")
    for recipe in nutrition_data["sample_recipes"]["low_calorie"]:
        print(f"\n{recipe['name']}")
        print(f"Calories: {recipe['nutrition']['calories']}")
        print(f"Rating: {recipe['avg_rating']:.1f}")

def format_recipe_output(recipes: List[Dict[str, Any]], query_type: str) -> None:
    if not recipes:
        print(f"\nNo recipes found for {query_type}")
        return

    print(f"\nFound {len(recipes)} recipes:")
    for recipe in recipes:
        print("\n" + "-"*50)

        # Display IDs - handle both types
        if 'original_id' in recipe:
            print(f"Recipe ID: {recipe['original_id']}")
        if '_id' in recipe:
            print(f"MongoDB ID: {recipe['_id']}")

        print(f"Name: {recipe.get('name', 'N/A')}")

        # Cooking time with formatted display
        if 'minutes' in recipe:
            time_str = f"{recipe['minutes']} minutes"
            if recipe['minutes'] >= 60:
                hours = recipe['minutes'] // 60
                remaining_mins = recipe['minutes'] % 60
                time_str = f"{hours} hour{'s' if hours > 1 else ''}"
                if remaining_mins > 0:
                    time_str += f" {remaining_mins} minute{'s' if remaining_mins > 1 else ''}"
            print(f"Cooking Time: {time_str}")

        if 'avg_rating' in recipe:
            print(f"Rating: {recipe.get('avg_rating', 0):.1f}")

        if 'ingredients' in recipe:
            print("Ingredients:")
            # Format ingredients in a more readable way, 3 per line
            ingredients = recipe['ingredients']
            for i in range(0, len(ingredients), 3):
                print(f"  {', '.join(ingredients[i:i+3])}")

        if 'nutrition' in recipe:
            print("Nutrition:")
            for key, value in recipe['nutrition'].items():
                print(f"  {key.replace('_', ' ').title()}: {value}")

        if 'tags' in recipe:
            print(f"Tags: {', '.join(recipe['tags'])}")

        if 'match_score' in recipe:
            print(f"Match Score: {recipe['match_score']}")

        if 'common_ingredients' in recipe:
            print(f"Common Ingredients: {recipe['common_ingredients']}")

        # Add tip for similar recipes - use original_id if available, otherwise use _id
        if 'original_id' in recipe:
            print(f"Tip: Use 'similar {recipe['original_id']}' to find similar recipes")
        elif '_id' in recipe:
            print(f"Tip: Use 'similar {recipe['_id']}' to find similar recipes")

def format_sentiment_output(sentiment_data: Dict[str, Any]) -> None:
    if not sentiment_data:
        print("\nNo sentiment data available")
        return

    print(f"\nSentiment Analysis for {sentiment_data['recipe_name']}")
    print(f"Average Rating: {sentiment_data['avg_rating']:.2f}")
    print(f"Review Count: {sentiment_data['review_count']}")
    print(f"Average Sentiment: {sentiment_data['avg_sentiment']:.2f}")
    print(f"Average Subjectivity: {sentiment_data['avg_subjectivity']:.2f}")

    print("\nSentiment Distribution:")
    for category, count in sentiment_data['sentiment_distribution'].items():
        print(f"{category.title()}: {count}")

    print("\nTop Reviews by Sentiment Strength:")
    for review in sentiment_data['sample_reviews']:
        print("\n" + "-"*50)
        print(f"Rating: {review['rating']}")
        print(f"Sentiment: {review['polarity']:.2f}")
        print(f"Review: {review['review']}")
