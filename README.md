# RecipeHub Intelligence Platform

A production-grade data engineering system that aggregates, processes, and analyzes 500,000+ recipes from multiple sources using MongoDB, demonstrating scalable NoSQL design, ETL pipelines, and real-time analytics.

## 🎯 Project Overview

**Problem:** Recipe data across the web is fragmented, inconsistent, and lacks comprehensive nutritional information. Existing platforms don't provide advanced filtering, trend analysis, or personalized recommendations at scale.

**Solution:** Built a unified recipe intelligence platform that:
- Processes 500k+ recipes from Kaggle Food.com dataset
- Implements efficient MongoDB schema design for sub-100ms query performance
- Provides CLI interface with 10+ advanced query capabilities
- Includes sentiment analysis, trend detection, and recommendation engine

**Technical Achievement:** Designed for scale - handles half a million documents with complex aggregation pipelines while maintaining fast query response times through strategic indexing.

## 🏗️ Technical Architecture

### Data Engineering Pipeline
```
Kaggle Dataset (500k+ records)
    ↓
Data Cleaning & Transformation
    ↓
MongoDB (Optimized Schema + Indexes)
    ↓
Aggregation Pipelines & Analytics
    ↓
CLI Application (User Interface)
```

### Technology Stack
- **Database:** MongoDB (NoSQL document store)
- **Data Processing:** Python, Pandas, PyMongo
- **Infrastructure:** Docker, Docker Compose
- **Data Source:** Kaggle Food.com dataset (500k+ recipes, millions of interactions)

### MongoDB Design Decisions

**Schema Design:**
- **Embedded Documents:** Recipe reviews stored as embedded array for 1-to-few relationships (fast read performance)
- **Referenced Reviews:** Separate reviews collection for complex analytics
- **Denormalized Stats:** Pre-calculated aggregations (avg_rating, review_count) for instant access

**Performance Optimizations:**
- Text indexes on name and ingredients for full-text search
- Compound indexes on nutrition fields for filtered queries
- Time-based indexes on review dates for trend analysis
- Strategic use of aggregation pipelines vs. simple queries

**Why MongoDB?**
- Flexible schema handles varying recipe structures (some have 5 ingredients, others have 50)
- Powerful aggregation framework for analytics (sentiment analysis, trends)
- Horizontal scalability for growing dataset
- Native support for embedded documents matches recipe data model

## 🚀 Features

### Core Functionality
- **Multi-criteria Search:** Filter by ingredients, cuisine, cooking time, nutritional values
- **Nutritional Analysis:** Track macros, calories, dietary restrictions across user history
- **Recommendation Engine:** Personalized suggestions based on user preferences and ratings
- **Sentiment Analysis:** Analyze review sentiment and subjectivity using NLP
- **Trend Detection:** Identify popular recipes and seasonal patterns
- **Similar Recipe Finder:** Content-based similarity using ingredient matching

### Advanced Queries
- Aggregation pipelines for complex analytics
- Real-time statistics calculation
- Dietary restriction filtering (vegetarian, vegan, low-calorie, etc.)
- Time-series trend analysis

## 📊 Scale & Performance

- **Dataset Size:** 500,000+ recipes
- **Interactions:** Millions of user reviews and ratings
- **Query Performance:** <100ms for most queries with proper indexing
- **Data Processing:** Handles batch ingestion of 500k records with progress tracking

## 🛠️ Technical Highlights

### Data Pipeline (`data-creation.py`)
- Kaggle API integration for dataset download
- ETL pipeline with data cleaning and transformation
- Nutrition data parsing from string lists to structured dictionaries
- Automated index creation for optimal performance
- Recipe statistics calculation using aggregation framework

### Application Architecture (`app.py`, `recipe_app.py`)
- Clean separation of concerns (CLI, business logic, formatting)
- Command parser with flexible parameter handling
- Error handling and user-friendly error messages
- Modular formatter system for different output types

### MongoDB Operations
```python
# Example: Complex aggregation for trend analysis
pipeline = [
    {"$match": {"date": {"$gte": thirty_days_ago}}},
    {"$group": {
        "_id": "$recipe_id",
        "avg_rating": {"$avg": "$rating"},
        "review_count": {"$sum": 1}
    }},
    {"$sort": {"review_count": -1}},
    {"$limit": 10}
]
```

## 📦 Prerequisites

- Docker & Docker Compose
- 2GB+ RAM (for MongoDB)
- Internet connection (initial data download ~200MB)

## ⚙️ Setup & Installation

### 1. Clone and Start Services
```bash
git clone <your-repo-url>
cd recipe-hub
docker-compose up -d
```

### 2. Initialize Database (REQUIRED - First Time Only)
```bash
docker exec -it recipe-cli bash
python data-creation.py
```

This downloads and processes the full dataset. Takes 10-15 minutes.

### 3. Run Application
```bash
# From within container
python app.py
```

## 💻 Usage Examples

### Search Recipes
```bash
search chocolate cake --limit 3
time 30                          # Recipes under 30 minutes
cuisine italian
```

### Nutritional Analysis
```bash
nutrition calories 500           # Low-calorie recipes
nutrition protein 20             # High-protein recipes  
analyze_nutrition user_12345     # User's nutritional patterns
```

### Recommendations & Discovery
```bash
similar 123456                   # Find similar recipes by ID
recommend user_12345             # Personalized recommendations
diet vegetarian                  # Filter by dietary restrictions
```

### Analytics
```bash
trends 30                        # Analyze last 30 days
sentiment "chocolate chip cookies"  # Review sentiment analysis
```

## 🎓 Learning Outcomes & Design Rationale

### Why This Approach?

**MongoDB over SQL:**
- Recipe data has variable structure (not all recipes have same fields)
- Embedded documents model naturally fits recipe → reviews relationship  
- Aggregation framework more intuitive for analytics than complex JOINs
- Easier horizontal scaling as dataset grows

**CLI over Web App:**
- Focuses demonstration on data engineering and database design
- Easier to showcase query complexity
- Faster development cycle for portfolio project

**Docker Infrastructure:**
- Reproducible environment
- Easy deployment and testing
- Mirrors production containerization practices

## 🔧 Project Structure
```
.
├── app.py                 # CLI entry point and command router
├── recipe_app.py          # Core MongoDB operations and business logic
├── data-creation.py       # ETL pipeline and database initialization
├── formatters.py          # Output formatting utilities
├── docker-compose.yml     # Container orchestration
├── Dockerfile            # Python environment setup
└── requirements.txt       # Python dependencies
```

## 🐛 Troubleshooting

**MongoDB connection errors:**
```bash
docker ps                     # Verify containers running
docker logs mymongo          # Check MongoDB logs
```

**No recipes found:**
```bash
python data-creation.py      # Re-initialize database
```

**Import errors:**
```bash
docker exec -it recipe-cli bash    # Ensure you're in container
pip install -r requirements.txt    # Reinstall dependencies
```

## 🚀 Future Enhancements

- [ ] Machine learning for better recommendations (collaborative filtering)
- [ ] Image recognition for ingredient detection  
- [ ] REST API for web/mobile integration
- [ ] GraphQL layer for flexible querying
- [ ] Real-time recipe trending with streaming analytics
- [ ] Integration with additional recipe APIs (Spoonacular, Edamam)

## 📝 Project Context

Built as capstone project for NoSQL Database course (Vanderbilt University Data Science MS Program). Demonstrates production-grade data engineering practices including schema design, performance optimization, ETL pipelines, and analytical query patterns on real-world data at scale.

## 🤝 Contributing

This is a portfolio/educational project, but suggestions and feedback are welcome via issues.

## 📄 License

MIT License - feel free to use for learning and reference

---

**Tech Stack:** MongoDB • Python • Docker • PyMongo • Pandas • Data Engineering
