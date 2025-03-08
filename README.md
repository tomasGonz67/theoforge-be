# TheoForge Backend

A FastAPI-based backend service with PostgreSQL and Neo4j databases, and pgAdmin for PostgreSQL management.

### Prerequisites
- Docker and Docker Compose
- Git

### Setup and Running

1. Clone the repository:
```bash
git clone https://github.com/tomasGonz67/theoforge-be.git
cd theoforge-be
```

2. Start the services:
```bash
docker compose up -d --build
```

This command will:
- Build and start all services defined in docker-compose.yml
- Automatically run database migrations using Alembic when the API service starts
- Make the API available at http://localhost:8000

### Services

The following services will be available:

- **FastAPI Application**: http://localhost:8000
  - API Documentation: http://localhost:8000/docs
  - Health Check: http://localhost:8000/health
  - Neo4j Hello World: http://localhost:8000/neo4j/hello-world
  - Neo4j Health Check: http://localhost:8000/neo4j/health

- **pgAdmin**:
  - URL: http://localhost:5050
  - Email: admin@example.com
  - Password: adminpassword

- **Neo4j Browser**:
  - URL: http://localhost:7474
  - Connect URL: neo4j://localhost:7687
  - Username: neo4j
  - Password: password

### Database Connection in pgAdmin

To connect to PostgreSQL using pgAdmin:

1. Access pgAdmin at http://localhost:5050
2. Login with the credentials above
3. Add a new server:
   - Name: Any name you prefer
   - Host: postgres
   - Port: 5432
   - Database: theoforge_dev
   - Username: user
   - Password: password

### Neo4j Browser Usage

To use Neo4j Browser:

1. Access Neo4j Browser at http://localhost:7474
2. Connect with:
   - URL: neo4j://localhost:7687
   - Username: neo4j
   - Password: password
3. Run Cypher queries, for example:
   ```cypher
   // Retrieve the Hello World message
   MATCH (message:Message)
   WHERE message.text = 'Hello, World!'
   RETURN message
   
   // View all nodes
   MATCH (n) RETURN n LIMIT 25
   ```

## Development

The project uses:
- FastAPI for the web framework
- PostgreSQL for relational data storage
- Neo4j for graph database functionality
- pgAdmin for PostgreSQL management
- Docker for containerization

### Development Commands

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Rebuild and start services (when you make changes to Dockerfile or requirements)
docker compose up -d --build

# View logs
docker compose logs -f  # All services
docker compose logs -f api  # Just the API service
```

### Database Commands

```bash
# Reset database (removes all data and volumes)
docker compose down -v

# Create a new migration
docker compose exec api alembic revision --autogenerate -m "description of changes"
```

Note: Database migrations are now automatically applied when the API service starts. You no longer need to manually run `docker compose exec api alembic upgrade head`.

### Testing Commands

```bash
# Run all tests
docker compose exec api pytest

# Run specific test file
docker compose exec api pytest tests/path/to/test_file.py
```

### Common Development Workflow

1. Make code changes
2. Reset database state (if needed):
   ```bash
   docker compose down -v
   docker compose up -d
   ```
3. Run tests:
   ```bash
   docker compose exec api pytest --cov
   ```
4. If tests pass, commit your changes

### Troubleshooting

If you encounter issues:

1. Check logs:
   ```bash
   docker compose logs -f
   ```

2. Reset everything and rebuild:
   ```bash
   docker compose down -v
   docker compose up -d --build
   ```

3. Verify database connections:
   ```bash
   # Check API health endpoints
   curl http://localhost:8000/health
   curl http://localhost:8000/neo4j/health
   ```

## Authentication

This API uses JWT token-based authentication:

1. **Registration**: Create a new user account using `/auth/register`
2. **Login**: Obtain a JWT token by submitting credentials to `/auth/login`
3. **Using Protected Routes**: Include the JWT token in the `Authorization` header as a Bearer token:
   ```
   Authorization: Bearer <your_jwt_token>
   ```

JWT tokens contain claims about the user, including:
- `sub`: The user's email
- `role`: The user's role (USER or ADMIN)
- `exp`: Token expiration timestamp

## API Endpoints

### Neo4j Endpoints
- `GET /neo4j/hello-world`: Creates a "Hello, World!" node in Neo4j and returns it
- `GET /neo4j/health`: Verifies Neo4j connection is working

### Authentication Endpoints
- `POST /auth/register`: Register a new user
- `POST /auth/login`: Login and obtain a JWT token
- `GET /auth/auth`: Test authentication (protected route)
- `POST /auth/logout`: Logout (frontend handles token disposal)

### Guest Endpoints
- `GET /guests`: Retrieve all guests
- `POST /guests`: Create a new guest
- `GET /guests/{guest_id}`: Retrieve a specific guest by ID
- `GET /guests/session/{session_id}`: Retrieve guests by session ID
- `PUT /guests/{guest_id}`: Update a guest by ID
- `PUT /guests/session/{session_id}`: Update a guest by session ID
- `DELETE /guests/{guest_id}`: Delete a guest by ID
- `DELETE /guests/session/{session_id}`: Delete a guest by session ID
- `POST /guests/{guest_id}/chat`: Update a guest's conversation

### Other Endpoints
- `GET /`: Returns "Hello World"
- `GET /health`: Health check endpoint that also verifies database connectivity

## Project Structure

```
.
├── app/                       # Main application package
│   ├── core/                  # Core functionality
│   │   └── security.py        # Password hashing and security utilities
│   ├── models/                # Database models (SQLAlchemy)
│   │   └── ...                # User, Guest models
│   ├── operations/            # Business logic operations
│   │   └── ...                # User, Guest, and JWT services
│   ├── routers/               # API route definitions     
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── dependencies.py    # Router dependencies (auth, DB)
│   │   └── guest.py           # Guest endpoints
│   ├── schemas/               # Pydantic schemas for validation
│   │   └── ...                # Request/response models
│   ├── database.py            # Database configuration and session
│   └── main.py                # FastAPI application entry point
├── alembic/                   # Database migrations
│   └── ...                    # Migration configuration and versions
├── settings/                  # Application settings
│   └── config.py              # Configuration settings
├── tests/                     # Test suite
│   ├── e2e/                   # End-to-end tests
│   ├── integration/           # Integration tests
│   ├── unit/                  # Unit tests
│   └── conftest.py            # Test fixtures and configuration
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Docker image definition
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

The codebase follows a structured organization:

- **Models**: Define database tables and relationships using SQLAlchemy ORM
- **Schemas**: Define request/response validation using Pydantic models
- **Operations**: Business logic and services for each domain entity
- **Routers**: API endpoints organized by feature
- **Dependencies**: Shared dependencies for authentication and database access

This structure separates concerns, making the codebase more maintainable and testable. 