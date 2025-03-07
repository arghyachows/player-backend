# Player Management API

A FastAPI-based REST API for managing players with JWT authentication.

## Features

- User authentication (signup, login, logout)
- JWT token-based authentication
- CRUD operations for players
- PostgreSQL database with SQLAlchemy ORM
- Pydantic models for request/response validation

## Prerequisites

- Python 3.8+
- PostgreSQL
- pip (Python package manager)

## Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd player-backend
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a PostgreSQL database named `player_db`

5. Update the `.env` file with your database credentials and JWT settings:

```
DATABASE_URL=postgresql://username:password@localhost:5432/player_db
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Running the Application

1. Start the FastAPI server:

```bash
uvicorn main:app --reload
```

2. Access the API documentation at: http://localhost:8000/docs

## API Endpoints

### Authentication

- POST `/signup` - Create a new user account
- POST `/token` - Login and get access token
- POST `/logout` - Logout (requires authentication)

### Players

- POST `/players/` - Create a new player (requires authentication)
- GET `/players/` - List all players (requires authentication)
- GET `/players/{player_id}` - Get a specific player (requires authentication)
- PUT `/players/{player_id}` - Update a player (requires authentication)
- DELETE `/players/{player_id}` - Delete a player (requires authentication)

## Example Usage

1. Create a new user:

```bash
curl -X POST "http://localhost:8000/signup" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "username": "testuser", "password": "password123"}'
```

2. Login and get access token:

```bash
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=testuser&password=password123"
```

3. Create a new player (using the access token):

```bash
curl -X POST "http://localhost:8000/players/" \
     -H "Authorization: Bearer <your-access-token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "John Doe", "position": "Forward", "team": "Team A", "age": 25, "jersey_number": 10}'
```
