# 🏗️ Infrastructure Setup Guide

## 📋 Overview

CryptoPredict MVP supports two development modes:
- **Local Development**: PostgreSQL and Redis running on your machine
- **Docker Development**: All services running in containers

Both modes automatically read configuration from `.env` file and can be switched seamlessly.

---

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd cryptopredict-mvp

# Copy and configure environment file
cp .env.example .env
# Edit .env with your specific settings
```

### 2. Choose Development Mode

**Option A: Local Development (Recommended for active development)**
```bash
# Use the development mode switcher
chmod +x dev-mode-switcher.sh
./dev-mode-switcher.sh local
```

**Option B: Docker Development**
```bash
./dev-mode-switcher.sh docker
```

### 3. Start Development Servers

```bash
# Terminal 1 - Backend
./start-backend-local.sh

# Terminal 2 - Frontend  
./start-frontend-local.sh
```

---

## 🔧 Local Development Setup

### Prerequisites

- **PostgreSQL** (any port, default: 5433)
- **Redis** (default: 6379)
- **Python 3.8+** with virtual environment
- **Node.js** 16+ with npm

### Configuration

The system automatically detects your local services. Update `.env` file:

```env
# Local Development Configuration
DATABASE_URL=postgresql://USERNAME:PASSWORD@localhost:PORT/cryptopredict
REDIS_URL=redis://127.0.0.1:6379/0
ENVIRONMENT=development
DEBUG=true
```

### Database Setup

```bash
# Create database (adjust port/credentials as needed)
createdb -h localhost -p 5433 -U postgres cryptopredict

# Tables are automatically created from models (no Alembic required)
# When you start the backend, tables will be created/updated
```

---

## 🐳 Docker Development Setup

### Prerequisites

- **Docker** and **Docker Compose**

### Configuration

```env
# Docker Development Configuration
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/cryptopredict
REDIS_URL=redis://redis:6379/0
ENVIRONMENT=development
DEBUG=true
```

### Container Management

```bash
# Start containers
docker-compose -f docker-compose-backend.yml up -d

# Stop containers
docker-compose -f docker-compose-backend.yml down

# View logs
docker-compose -f docker-compose-backend.yml logs
```

---

## 🔄 Switching Between Modes

### Development Mode Switcher

```bash
# Switch to local development
./dev-mode-switcher.sh local

# Switch to Docker development
./dev-mode-switcher.sh docker

# Check current status
./dev-mode-switcher.sh status
```

### What the Switcher Does

- **Automatic Backup**: Saves current configuration before switching
- **Smart Restore**: Restores previous configurations when switching back
- **Service Management**: Stops/starts appropriate services
- **Environment Update**: Updates `.env` file automatically

---

## 🌐 Access Points

Once services are running:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Next.js application |
| **Backend API** | http://localhost:8000 | FastAPI application |
| **API Documentation** | http://localhost:8000/docs | Swagger UI |
| **Alternative API Docs** | http://localhost:8000/redoc | ReDoc UI |

### Docker-only Services
| Service | URL | Credentials |
|---------|-----|-------------|
| **PgAdmin** | http://localhost:5050 | admin@cryptopredict.local / admin123 |
| **Redis Commander** | http://localhost:8081 | No authentication |

---

## 📁 Project Structure

```
cryptopredict-mvp/
├── backend/                 # FastAPI backend
│   ├── app/                # Application code
│   │   ├── core/           # Configuration and database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── api/            # API endpoints
│   │   └── ml/             # Machine learning modules
│   ├── alembic/            # Database migrations (optional)
│   ├── alembic.ini         # Alembic configuration (reads from env)
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend
│   ├── src/                # Source code
│   │   ├── app/           # App Router pages
│   │   ├── components/    # React components
│   │   └── lib/           # Utilities
│   └── package.json       # Node.js dependencies
├── docs/                   # Documentation
├── .env                    # Environment variables (auto-managed)
├── .env.example           # Environment template
├── dev-mode-switcher.sh   # Development mode switcher
├── start-backend-local.sh # Backend startup script
└── start-frontend-local.sh # Frontend startup script
```

---

## ⚙️ Environment Variables

### Core Configuration

| Variable | Description | Local Example | Docker Example |
|----------|-------------|---------------|----------------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://postgres:admin123@localhost:5433/cryptopredict` | `postgresql://postgres:postgres123@postgres:5432/cryptopredict` |
| `REDIS_URL` | Redis connection | `redis://127.0.0.1:6379/0` | `redis://redis:6379/0` |
| `ENVIRONMENT` | Environment mode | `development` | `development` |
| `DEBUG` | Debug mode | `true` | `true` |

### Security Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Application secret | Auto-generated |
| `JWT_SECRET_KEY` | JWT signing key | Auto-generated |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `30` |

### External APIs

| Variable | Description | Required |
|----------|-------------|----------|
| `COINGECKO_API_KEY` | CoinGecko API key | Optional |
| `BINANCE_API_KEY` | Binance API key | Optional |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key | Optional |

---

## 🗄️ Database Management

### Automatic Table Creation

Tables are automatically created from SQLAlchemy models when the backend starts. No manual migration required for development.

```python
# Models are defined in backend/app/models/
from app.models import User, Cryptocurrency, PriceData, Prediction
```

### Manual Database Operations

```bash
# Connect to local database
psql -h localhost -p 5433 -U postgres -d cryptopredict

# Connect to Docker database
docker-compose exec postgres psql -U postgres -d cryptopredict

# Create database backup
pg_dump -h localhost -p 5433 -U postgres cryptopredict > backup.sql
```

### Optional: Alembic Migrations

If you prefer to use Alembic for database migrations:

```bash
cd backend

# Initialize Alembic (if not already done)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

**Note**: Alembic configuration automatically reads `DATABASE_URL` from environment.

---

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5433

# Check credentials and database exists
psql -h localhost -p 5433 -U postgres -l
```

#### Redis Connection Failed
```bash
# Check if Redis is running
redis-cli ping

# Check Redis configuration
redis-cli config get "*"
```

#### Docker Issues
```bash
# Check container status
docker-compose -f docker-compose-backend.yml ps

# View container logs
docker-compose -f docker-compose-backend.yml logs postgres
docker-compose -f docker-compose-backend.yml logs redis

# Restart containers
docker-compose -f docker-compose-backend.yml restart
```

#### Port Conflicts
```bash
# Check what's using a port
netstat -tulpn | grep :5433
netstat -tulpn | grep :6379

# Kill process using port
sudo kill -9 $(lsof -ti:5433)
```

### Development Mode Status

```bash
# Check current development mode
./dev-mode-switcher.sh status

# This shows:
# - Current configuration (Local vs Docker)
# - Service status (PostgreSQL, Redis, Docker containers)
# - Available backups
# - Environment details
```

### Reset Everything

```bash
# Stop all services
./dev-mode-switcher.sh local
docker-compose -f docker-compose-backend.yml down

# Remove containers and volumes (⚠️ Data will be lost)
docker-compose -f docker-compose-backend.yml down -v
docker system prune

# Restore from backup if needed
cp .env.local.backup .env  # or .env.docker.backup
```

---

## 📈 Performance Tips

### Local Development
- Use local PostgreSQL and Redis for faster response times
- Enable debug mode for detailed error messages
- Use hot reload for both frontend and backend

### Docker Development  
- Use Docker development mode for testing production-like environment
- Allocate sufficient memory to Docker (4GB+ recommended)
- Use volumes for persistent data

### General
- Keep your `.env` file secure and never commit it to version control
- Use environment-specific configurations
- Monitor logs for performance bottlenecks

---

## 🔒 Security Considerations

### Development Environment
- Use strong passwords even in development
- Keep API keys in `.env` file, never in code
- Use HTTPS in production
- Regularly update dependencies

### Production Deployment
- Change all default passwords
- Use environment variables for sensitive data
- Enable SSL/TLS encryption
- Configure proper CORS origins
- Set up proper logging and monitoring

---

## 📞 Getting Help

### Useful Commands

```bash
# Check environment status
./dev-mode-switcher.sh status

# Test database connection
python -c "from app.core.database import engine; engine.connect()"

# Check configuration
python -c "from app.core.config import settings; print(settings.DATABASE_URL)"
```

### Log Files

- **Backend logs**: Console output or `./logs/app.log`
- **Frontend logs**: Console output
- **Docker logs**: `docker-compose logs`

For additional help, check the project repository issues or create a new issue with:
- Current environment status output
- Error messages
- Steps to reproduce the issue