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
docker-compose up --build
```

### Services

The following services will be available:

- **FastAPI Application**: http://localhost:8000
  - API Documentation: http://localhost:8000/docs
  - Health Check: http://localhost:8000/health

- **PostgreSQL Database**:
  - Host: localhost
  - Port: 5432
  - Database: theoforge
  - Username: user
  - Password: password

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
   - Database: theoforge
   - Username: user
   - Password: password

## Development

The project uses:
- FastAPI for the web framework
- PostgreSQL for the database
- pgAdmin for database management
- Docker for containerization

## API Endpoints

- `GET /`: Returns "Hello World"
- `GET /health`: Health check endpoint that also verifies database connectivity

## Project Structure

```
.
├── app/
│   └── main.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
``` 