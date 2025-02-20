# TheoForge Backend

A FastAPI-based backend service for user management.

## Project Structure
```
app/
├── main.py          # Application entry point
├── database.py      # Database configuration
├── dependencies.py  # Database sessions, auth, and access control
├── models/         # Database models
├── routers/        # API endpoints
├── schemas/        # Data validation
└── services/       # Business logic

alembic/            # Database migrations
tests/              # Test files
```

## Prerequisites

- Python 3.10 or higher
- PostgreSQL 16
- pgAdmin 4 (optional, for database management)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/tomasGonz67/theoforgeBackend.git
cd theoforgeBackend
```

2. Create and activate virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Copy `.env.example` to `.env` and update the values:
```bash
cp .env.example .env
```
Then edit `.env` with your specific configuration:
- Set your PostgreSQL password in the `DATABASE_URL`
- Change `JWT_SECRET_KEY` to a secure random string
- Adjust other settings as needed

5. Create database:
- Using pgAdmin 4 or psql, create a new database named `theoforge_dev`
- Run database migrations:
```bash
alembic upgrade head
```

## Running the Application

Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`

## API Documentation

Once the server is running, you can access:
- Swagger UI documentation: `http://127.0.0.1:8000/docs`
- ReDoc documentation: `http://127.0.0.1:8000/redoc`

### Available Endpoints

- `POST /register` - Register a new user
- `POST /token` - Login and get access token
- `GET /users/me` - Get current user information (requires authentication)

## Development

Built with:
- FastAPI - Framework
- PostgreSQL - Database
- SQLAlchemy - ORM with async support
- Alembic - Database migrations
- JWT - Authentication
- Pydantic - Data validation

## Testing

Run tests using pytest:
```bash
pytest
```

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Run tests
4. Submit a pull request

### Reference
- [User Management](https://github.com/kaw393939/user_management)
