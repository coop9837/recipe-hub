from recipe_app import RecipeApp
from formatters import (
    format_recipe_output,
    format_sentiment_output,
    format_trend_output,
    format_nutrition_analysis
)

class RecipeCLI:
    def __init__(self):
        self.app = RecipeApp()
        
    def print_help(self):
        """Print available commands and their usage"""
        print("\nAvailable commands:")
        print("Basic Queries:")
        print("1. search <ingredient/recipe name> - Search recipes by name or ingredients")
        print("2. time <minutes> - Find recipes taking less than specified minutes")
        print("3. cuisine <type> - Search recipes by cuisine type")

        print("\nNutritional Queries:")
        print("4. nutrition <nutrient> <max_value> - Find recipes by nutritional criteria")
        print("5. analyze_nutrition [user_id] - Analyze nutritional patterns")

        print("\nRecommendations and Similar Recipes:")
        print("6. similar <recipe_id> - Find similar recipes")
        print("7. recommend <user_id> - Get personalized recommendations")

        print("\nAnalysis:")
        print("8. trends [days=30] - Analyze recipe trends")
        print("9. sentiment <recipe_name> - Detailed sentiment analysis")
        print("10. diet <restriction> - Find recipes by dietary restriction")

        print("\nOther Commands:")
        print("11. help - Show this help message")
        print("12. exit - Exit the application")
        print("\nAdd --limit N to any command to change number of results (default: 5)")

    def run(self):
        """Main CLI loop"""
        print("\nWelcome to the RecipeHub CLI!")
        self.print_help()

        while True:
            try:
                command = input("\nEnter command: ").strip().split()
                if not command:
                    continue

                if command[0] == 'exit':
                    break
                elif command[0] == 'help':
                    self.print_help()
                    continue

                # Handle limit parameter
                limit = 5
                if '--limit' in command:
                    limit_index = command.index('--limit')
                    if len(command) > limit_index + 1:
                        limit = int(command[limit_index + 1])
                        command = command[:limit_index] + command[limit_index + 2:]

                # Process commands
                if command[0] == 'search' and len(command) > 1:
                    results = self.app.search_recipes(' '.join(command[1:]), limit)
                    format_recipe_output(results, f"search term '{' '.join(command[1:])}'")
                
                elif command[0] == 'time' and len(command) > 1:
                    if command[1].isdigit():
                        results = self.app.find_by_cooking_time(int(command[1]), limit)
                        format_recipe_output(results, f"cooking time <= {command[1]} minutes")
                    else:
                        print("Error: Cooking time must be a number")
                
                elif command[0] == 'cuisine' and len(command) > 1:
                    results = self.app.find_by_cuisine(command[1], limit)
                    format_recipe_output(results, f"cuisine type: {command[1]}")
                
                elif command[0] == 'nutrition' and len(command) > 2:
                    try:
                        value = float(command[2])
                        results = self.app.find_by_nutrition(command[1], value, limit)
                        format_recipe_output(results, f"{command[1]} <= {value}")
                    except ValueError:
                        print("Error: Nutritional value must be a number")
                
                elif command[0] == 'analyze_nutrition':
                    user_id = command[1] if len(command) > 1 else None
                    results = self.app.analyze_nutritional_patterns(user_id)
                    if results["overall_stats"] is None:
                        print("\nNo nutritional data available.")
                    else:
                        format_nutrition_analysis(results)
                
                elif command[0] == 'similar' and len(command) > 1:
                    results = self.app.find_similar_recipes(command[1], limit)
                    format_recipe_output(results, f"similar to recipe {command[1]}")
                
                elif command[0] == 'recommend' and len(command) > 1:
                    results = self.app.get_personalized_recommendations(command[1], limit)
                    format_recipe_output(results, f"recommendations for user {command[1]}")
                
                elif command[0] == 'trends':
                    days = int(command[1]) if len(command) > 1 and command[1].isdigit() else 30
                    results = self.app.analyze_trends(days)
                    format_trend_output(results)
                
                elif command[0] == 'sentiment' and len(command) > 1:
                    results = self.app.analyze_sentiment_detailed(' '.join(command[1:]))
                    format_sentiment_output(results)
                
                elif command[0] == 'diet' and len(command) > 1:
                    diet_restriction = command[1].lower()
                    results = self.app.find_by_diet(diet_restriction, limit)
                    format_recipe_output(results, f"dietary restriction: {diet_restriction}")
                
                else:
                    print("Invalid command. Type 'help' to see available commands.")

            except Exception as e:
                print(f"An error occurred: {e}")
                print("Type 'help' to see available commands.")

        self.app.close()
        print("\nThanks for using Recipe Search CLI!")

def main():
    cli = RecipeCLI()
    cli.run()

