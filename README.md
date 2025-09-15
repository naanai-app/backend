# Place Recommendation Social Network API

A comprehensive backend application for a mobile place recommendation social network built with FastAPI, PostgreSQL, and Neo4j.

## Features

### Core Functionality
- **User Authentication**: Sign up with email, username, password, and city. Login with email and password.
- **Social Network**: Follow/unfollow users, mutual followers become "friends"
- **Place Management**: Create and manage place cards with categories, descriptions, locations, and Google Maps integration
- **Posts System**: Create posts with check-ins to places, like and comment on posts
- **User Lists**: Liked/disliked places lists, custom user-created lists
- **Search**: Advanced place search by text, categories, location, and filters
- **Profile Management**: Edit nickname, password, and city

### Technical Stack
- **Backend**: FastAPI with async/await support
- **SQL Database**: PostgreSQL with SQLAlchemy ORM
- **Graph Database**: Neo4j for social connections and recommendations
- **Authentication**: JWT tokens with bcrypt password hashing
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## Project Structure

```
app/
├── api/
│   └── v1/
│       ├── endpoints/
│       │   ├── auth.py          # Authentication endpoints
│       │   ├── users.py         # User management and social features
│       │   ├── places.py        # Place management
│       │   ├── categories.py    # Category management
│       │   ├── posts.py         # Posts, likes, comments
│       │   └── user_lists.py    # User lists management
│       └── api.py               # API router configuration
├── core/
│   ├── config.py               # Application settings
│   ├── database.py             # PostgreSQL database setup
│   ├── graph_db.py             # Neo4j graph database
│   ├── security.py             # Authentication utilities
│   └── deps.py                 # FastAPI dependencies
├── crud/
│   ├── user.py                 # User CRUD operations
│   ├── place.py                # Place CRUD operations
│   ├── category.py             # Category CRUD operations
│   ├── post.py                 # Post CRUD operations
│   └── user_list.py            # User list CRUD operations
├── models/
│   ├── user.py                 # User SQLAlchemy model
│   ├── place.py                # Place and category models
│   ├── post.py                 # Post, comment, like models
│   └── user_list.py            # User list models
├── schemas/
│   ├── user.py                 # User Pydantic schemas
│   ├── place.py                # Place and category schemas
│   ├── post.py                 # Post schemas
│   └── user_list.py            # User list schemas
└── main.py                     # FastAPI application entry point
```

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository and navigate to the backend directory
2. Copy the environment file:
   ```bash
   cp .env.example .env
   ```
3. Update the `.env` file with your configuration
4. Start all services (database will auto-initialize):
   ```bash
   docker-compose up -d
   ```
5. The API will be available at `http://localhost:8000`
6. API documentation at `http://localhost:8000/docs`
7. Create an admin user:
   ```bash
   make create-admin
   # or
   docker-compose exec app python scripts/create_admin.py
   ```

### Using Makefile Commands

```bash
make up           # Start all services
make logs         # View logs
make db-check     # Check database health
make create-admin # Create admin user
make shell        # Open shell in app container
make down         # Stop all services
make help         # Show all available commands
```

### Manual Setup

1. Install Python 3.11+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up PostgreSQL and Neo4j databases
4. Copy and configure `.env` file
5. Initialize database:
   ```bash
   python scripts/init_db.py
   ```
6. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - Create new user account
- `POST /api/v1/auth/login` - Login with email/password
- `POST /api/v1/auth/login/email` - Alternative login endpoint

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user profile
- `GET /api/v1/users/{user_id}` - Get user by ID
- `POST /api/v1/users/follow/{user_id}` - Follow a user
- `DELETE /api/v1/users/follow/{user_id}` - Unfollow a user
- `GET /api/v1/users/{user_id}/followers` - Get user's followers
- `GET /api/v1/users/{user_id}/following` - Get users being followed
- `GET /api/v1/users/{user_id}/friends` - Get mutual followers (friends)
- `GET /api/v1/users/{user_id}/stats` - Get user statistics
- `GET /api/v1/users/recommendations/users` - Get user recommendations

### Places
- `GET /api/v1/places/` - List places
- `POST /api/v1/places/` - Create new place
- `GET /api/v1/places/{place_id}` - Get place by ID
- `PUT /api/v1/places/{place_id}` - Update place
- `POST /api/v1/places/search` - Search places with filters

### Categories
- `GET /api/v1/categories/` - List categories
- `POST /api/v1/categories/` - Create new category
- `GET /api/v1/categories/{category_id}` - Get category by ID
- `PUT /api/v1/categories/{category_id}` - Update category
- `DELETE /api/v1/categories/{category_id}` - Delete category

### Posts
- `GET /api/v1/posts/` - List posts
- `POST /api/v1/posts/` - Create new post
- `GET /api/v1/posts/{post_id}` - Get post by ID
- `PUT /api/v1/posts/{post_id}` - Update post
- `DELETE /api/v1/posts/{post_id}` - Delete post
- `POST /api/v1/posts/{post_id}/like` - Like a post
- `DELETE /api/v1/posts/{post_id}/like` - Unlike a post
- `GET /api/v1/posts/{post_id}/comments` - Get post comments
- `POST /api/v1/posts/{post_id}/comments` - Add comment to post
- `PUT /api/v1/posts/comments/{comment_id}` - Update comment
- `DELETE /api/v1/posts/comments/{comment_id}` - Delete comment
- `GET /api/v1/posts/user/{user_id}` - Get posts by user

### User Lists
- `GET /api/v1/lists/` - Get current user's lists
- `POST /api/v1/lists/` - Create new list
- `GET /api/v1/lists/{list_id}` - Get list by ID
- `PUT /api/v1/lists/{list_id}` - Update list
- `DELETE /api/v1/lists/{list_id}` - Delete list
- `POST /api/v1/lists/{list_id}/items` - Add place to list
- `GET /api/v1/lists/{list_id}/items` - Get list items
- `PUT /api/v1/lists/items/{item_id}` - Update list item
- `DELETE /api/v1/lists/items/{item_id}` - Remove item from list
- `POST /api/v1/lists/quick-like/{place_id}` - Quick add to liked places
- `POST /api/v1/lists/quick-dislike/{place_id}` - Quick add to disliked places
- `GET /api/v1/lists/user/{user_id}` - Get public lists of a user

## Database Schema

### PostgreSQL Tables
- **users**: User accounts and profiles
- **places**: Place information and details
- **categories**: Place categories with colors
- **place_categories**: Many-to-many relationship between places and categories
- **posts**: User posts with optional place check-ins
- **comments**: Comments on posts (supports nested comments)
- **post_likes**: Post likes by users
- **user_lists**: User-created lists (liked, disliked, custom)
- **user_list_items**: Items in user lists with personal notes and ratings

### Neo4j Graph Schema
- **User nodes**: Represent users in the social network
- **FOLLOWS relationships**: Track user following relationships
- **Friend detection**: Mutual FOLLOWS relationships indicate friendship
- **Recommendations**: Based on mutual connections and graph traversal

## Configuration

Key environment variables:

- `POSTGRES_*`: PostgreSQL database connection
- `NEO4J_*`: Neo4j graph database connection
- `SECRET_KEY`: JWT token encryption key
- `GOOGLE_MAPS_API_KEY`: Optional Google Maps integration
- `BACKEND_CORS_ORIGINS`: Allowed CORS origins for frontend

## Database Management

### Initialization Scripts

The project includes comprehensive database management scripts:

#### Core Scripts
- **`scripts/init_db.py`** - Initialize database tables and seed data
- **`scripts/check_db.py`** - Check database health and connections
- **`scripts/seed_data.py`** - Seed initial categories and demo data
- **`scripts/create_admin.py`** - Create admin user interactively
- **`scripts/wait_for_db.py`** - Wait for database services (used in Docker)

#### Usage Examples

```bash
# Initialize database (creates tables and seeds data)
python scripts/init_db.py

# Check database health
python scripts/check_db.py

# Reset database (WARNING: deletes all data)
python scripts/init_db.py --reset

# Create admin user
python scripts/create_admin.py

# Seed demo data only
python scripts/seed_data.py
```

#### Convenience Scripts

**Linux/Mac:**
```bash
./scripts/run.sh init    # Initialize database
./scripts/run.sh check   # Check database health
./scripts/run.sh admin   # Create admin user
./scripts/run.sh dev     # Start development server
```

**Windows:**
```bash
scripts\run.bat init     # Initialize database
scripts\run.bat check    # Check database health
scripts\run.bat admin    # Create admin user
scripts\run.bat dev      # Start development server
```

#### Docker Commands

```bash
# Using Makefile (recommended)
make db-init      # Initialize database
make db-check     # Check database health
make create-admin # Create admin user
make db-seed      # Seed demo data
make db-reset     # Reset database

# Using docker-compose directly
docker-compose exec app python scripts/init_db.py
docker-compose exec app python scripts/check_db.py
docker-compose exec app python scripts/create_admin.py
```

### Initial Data

The database initialization includes:
- **12 predefined categories** with colors (Restaurant, Cafe, Bar, Shopping, etc.)
- **Demo user** (`demo@example.com` / `demo123`) for testing
- **5 sample places** in New York with proper categorization
- **Default user lists** (Liked Places, Disliked Places) for each user

## Development

### Adding New Features

1. Create database models in `app/models/`
2. Create Pydantic schemas in `app/schemas/`
3. Implement CRUD operations in `app/crud/`
4. Create API endpoints in `app/api/v1/endpoints/`
5. Register routes in `app/api/v1/api.py`

### Testing

```bash
pytest
# or with Docker
make test
```

### Database Migrations

The application uses SQLAlchemy with automatic table creation. For production, consider using Alembic for database migrations:

```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migration
alembic upgrade head
```

## Docker Services

The application runs with the following services:

- **app** (Port 8000): FastAPI application with auto-initialization
- **db** (Port 5432): PostgreSQL 15 database
- **neo4j** (Ports 7474, 7687): Neo4j 5.14 graph database with APOC plugins
- **redis** (Port 6379): Redis for caching (optional)

### Service Health Checks

All services include health checks to ensure proper startup order:
- PostgreSQL: `pg_isready` check
- Neo4j: Cypher shell connectivity test
- App: Waits for both databases before starting

### Auto-Initialization

The Docker setup automatically:
1. Waits for database services to be healthy
2. Creates database tables if they don't exist
3. Seeds initial data (categories, demo user, sample places)
4. Starts the FastAPI application

## Deployment

### Production Considerations

1. Use environment variables for all sensitive configuration
2. Set up proper SSL/TLS certificates
3. Configure database connection pooling
4. Set up monitoring and logging
5. Use a reverse proxy (nginx) for static files and load balancing
6. Consider using managed database services for PostgreSQL and Neo4j
7. Remove demo data and change default passwords
8. Set up backup strategies for both PostgreSQL and Neo4j

### Security Features

- JWT token-based authentication with configurable expiration
- Password hashing with bcrypt
- Input validation with Pydantic
- SQL injection protection with SQLAlchemy ORM
- CORS configuration for frontend integration
- Health check endpoints for monitoring

## API Documentation

Once the application is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

## Contributing

1. Follow the existing code structure and patterns
2. Add appropriate error handling and validation
3. Include docstrings for all functions and classes
4. Test your changes thoroughly
5. Update documentation as needed

## License

This project is licensed under the MIT License - see the LICENSE file for details.
