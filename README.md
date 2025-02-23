# TheoForge Backend

A FastAPI-based backend service with PostgreSQL database and pgAdmin for database management.

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

### Services

The following services will be available:

- **FastAPI Application**: http://localhost:8000
  - API Documentation: http://localhost:8000/docs
  - Health Check: http://localhost:8000/health

- **pgAdmin**:
  - URL: http://localhost:5050
  - Email: admin@example.com
  - Password: adminpassword

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

## Development

The project uses:
- FastAPI for the web framework
- PostgreSQL for the database
- pgAdmin for database management
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

# Run database migrations
docker compose exec api alembic upgrade head
```

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
   docker compose exec api alembic upgrade head
   ```
3. Run tests:
   ```bash
   docker compose exec api pytest
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
   docker compose exec api alembic upgrade head
   ```

3. Verify database connection:
   ```bash
   # Check API health endpoint
   curl http://localhost:8000/health
   ```

## API Endpoints

- `GET /`: Returns "Hello World"
- `GET /health`: Health check endpoint that also verifies database connectivity
- `POST /auth/register`: Register a new user

## Project Structure

```
.
├── app/
│   ├── auth/                    # Authentication components
│   │   ├── dependencies.py      
│   │   └── __init__.py
│   ├── core/                    
│   │   └── security.py         # Password hashing 
│   ├── models/                  # Database models
│   │   └── user.py            
│   ├── schemas/                 # Pydantic schemas
│   │   └── user.py            
│   ├── operations/             # Business logic operations
│   │   └── user.py            
│   ├── database.py            # Database configuration + session
│   └── main.py                # FastAPI application
├── alembic/                    # Database migrations
│   ├── versions/              
│   │   └── 
│   ├── env.py                
│   └── script.py.mako        
├── tests/                      # Test suite
│   ├── conftest.py            # Test fixtures + configuration
│   ├── integration/           # Integration tests
│   │   └── test_registration.py
│   └── unit/                  # Unit tests
│       └── test_user.py
├── alembic.ini               
├── docker-compose.yml         
├── Dockerfile                
├── requirements.txt          
└── README.md                
``` 