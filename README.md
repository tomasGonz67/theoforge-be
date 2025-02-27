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
docker-compose up -d --build
```

### Retesting Cookies
You will need to clear cookies in your browser for effective testing of cookie creation

### Services

The following services will be available:

- **FastAPI Application**: http://localhost:8000
  - API Documentation: http://localhost:8000/docs
  - Health Check: http://localhost:8000/health

  **Frontend Application**: http://localhost:5173

- **PostgreSQL Database**:
  - Host: localhost
  - Port: 5432
  - Database: theoforge_dev
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
   - Database: theoforge_dev
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
- `GET /login`: Login Method #1 (Preferred - 2-step process): Basic login endpoint with example users_db data that creates JWT access token
- `GET /login/cookie`: Login Method #2: Instantly sets cookie after creating access token and serves to frontend
- `GET /simple-cookie-test`: Endpoint to create example test cookie
- `GET /set-cookie`: Second step of Login Method #1: Endpoint to set cookie based on encoded access_token
- `GET /auth`: Endpoint to authenticate user based on cookie and access_token for a protected path


## Project Structure

```
theoforge-be
   ├─ app
   │  ├─ auth
   │  │  ├─ dependencies.py
   │  ├─ core
   │  ├─ main.py
   │  ├─ models
   │  ├─ operations
   │  ├─ routers
   │  │  ├─ auth.py
   │  ├─ schemas
   │  │  ├─ token_schema.py
   │  ├─ services
   │  │  ├─ jwt_service.py
   ├─ docker-compose.yml
   ├─ Dockerfile
   ├─ frontend
   │  ├─ eslint.config.js
   │  ├─ index.html
   │  ├─ package-lock.json
   │  ├─ package.json
   │  ├─ public
   │  │  └─ vite.svg
   │  ├─ README.md
   │  ├─ src
   │  │  ├─ api.ts
   │  │  ├─ App.css
   │  │  ├─ App.jsx
   │  │  ├─ assets
   │  │  │  └─ react.svg
   │  │  ├─ components
   │  │  │  ├─ Dashboard.tsx
   │  │  │  └─ Login.tsx
   │  │  ├─ index.css
   │  │  └─ main.jsx
   │  └─ vite.config.js
   ├─ README.md
   ├─ requirements.txt
   └─ settings
      ├─ config.py
``` 