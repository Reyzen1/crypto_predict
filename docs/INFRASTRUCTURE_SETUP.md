# CryptoPredict MVP - Infrastructure Setup Guide

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Git installed
- At least 4GB RAM available for containers

### 1. Initial Setup

```bash
# Clone and navigate to project
cd cryptopredict-mvp

# Copy environment file
cp .env.example .env

# Edit .env file with your settings (optional for development)
# nano .env  # Linux/Mac
# notepad .env  # Windows
```

### 2. Start the Development Environment

#### Linux/Mac:
```bash
# Make script executable
chmod +x scripts/docker-dev.sh

# Start all services
./scripts/docker-dev.sh start
```

#### Windows:
```batch
# Start all services
scripts\docker-dev.bat start
```

### 3. Verify Everything is Working

Check service status:
```bash
# Linux/Mac
./scripts/docker-dev.sh status

# Windows
scripts\docker-dev.bat status
```

Check database health:
```bash
# Run health check (requires Python with psycopg2 and redis packages)
python scripts/check-db.py
```

## 🌐 Access Points

Once everything is running, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Next.js application |
| **Backend API** | http://localhost:8000 | FastAPI application |
| **API Documentation** | http://localhost:8000/docs | Swagger UI |
| **Alternative API Docs** | http://localhost:8000/redoc | ReDoc UI |
| **PgAdmin** | http://localhost:5050 | PostgreSQL admin interface |
| **Redis Commander** | http://localhost:8081 | Redis admin interface |

### Default Credentials
- **PgAdmin**: admin@cryptopredict.local / admin123
- **PostgreSQL**: postgres / postgres123
- **Redis**: No password (development only)

## 📁 Project Structure

```
cryptopredict-mvp/
├── backend/                 # FastAPI backend
│   ├── app/                # Application code
│   ├── Dockerfile          # Production Docker image
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend
│   ├── app/               # App Router pages
│   ├── components/        # React components
│   ├── Dockerfile         # Production Docker image
│   ├── Dockerfile.dev     # Development Docker image
│   └── package.json       # Node.js dependencies
├── database/              # Database initialization
│   └── init.sql          # Initial database schema
├── redis/                 # Redis configuration
│   └── redis.conf        # Redis configuration file
├── scripts/               # Management scripts
│   ├── docker-dev.sh     # Linux/Mac management script
│   ├── docker-dev.bat    # Windows management script
│   └── check-db.py       # Database health check
├── logs/                  # Application logs
├── docker-compose.yml     # Multi-container configuration
├── .env.example          # Environment variables template
└── .env                  # Your environment variables
```

## 🔧 Common Commands

### Service Management
```bash
# Start all services
./scripts/docker-dev.sh start

# Start only databases
./scripts/docker-dev.sh start-db

# Start only backend
./scripts/docker-dev.sh start-backend

# Start only frontend
./scripts/docker-dev.sh start-frontend

# Stop all services
./scripts/docker-dev.sh stop

# View logs
./scripts/docker-dev.sh logs

# View backend logs only
./scripts/docker-dev.sh logs-backend
```

### Database Management
```bash
# Open PostgreSQL shell
./scripts/docker-dev.sh db-shell

# Open Redis shell
./scripts/docker-dev.sh redis-shell

# Create database backup
./scripts/docker-dev.sh backup
```

### Development Workflow
```bash
# Check service status
./scripts/docker-dev.sh status

# Reset everything (removes all data!)
./scripts/docker-dev.sh reset
```

## 🐳 Docker Services

### PostgreSQL Database
- **Image**: postgres:15-alpine
- **Port**: 5432
- **Database**: cryptopredict
- **Volume**: Persistent data storage
- **Health Check**: Automatic readiness verification

### Redis Cache
- **Image**: redis:7-alpine
- **Port**: 6379
- **Configuration**: Custom redis.conf
- **Volume**: Persistent data storage
- **Health Check**: Ping command verification

### Backend (FastAPI)
- **Build**: From ./backend/Dockerfile
- **Port**: 8000
- **Hot Reload**: Enabled in development
- **Dependencies**: PostgreSQL, Redis
- **Health Check**: HTTP endpoint verification

### Frontend (Next.js)
- **Build**: From ./frontend/Dockerfile.dev
- **Port**: 3000
- **Hot Reload**: Enabled in development
- **Dependencies**: Backend API
- **Proxy**: API calls routed to backend

## 🔍 Troubleshooting

### Common Issues

#### 1. Services Won't Start
```bash
# Check Docker is running
docker info

# Check for port conflicts
docker ps -a
netstat -tulpn | grep :3000  # Linux
netstat -an | findstr :3000  # Windows
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL logs
./scripts/docker-dev.sh logs-db

# Verify database is ready
docker-compose exec postgres pg_isready -U postgres
```

#### 3. Frontend Can't Connect to Backend
```bash
# Check backend is running
curl http://localhost:8000/health

# Check backend logs
./scripts/docker-dev.sh logs-backend
```

#### 4. Permission Issues (Linux/Mac)
```bash
# Fix script permissions
chmod +x scripts/docker-dev.sh

# Fix Docker permissions (if needed)
sudo usermod -aG docker $USER
# Then logout and login again
```

### Clean Reset
If everything is broken, reset completely:
```bash
# Stop and remove everything
./scripts/docker-dev.sh reset

# Remove all Docker images (optional)
docker image prune -a

# Start fresh
./scripts/docker-dev.sh start
```

## 📊 Health Monitoring

### Automatic Health Checks
All services include built-in health checks that Docker monitors automatically.

### Manual Health Verification
```bash
# Check all services
./scripts/docker-dev.sh status

# Detailed database check
python scripts/check-db.py

# Check individual services
curl http://localhost:8000/health  # Backend
curl http://localhost:3000         # Frontend
```

## 🔐 Security Notes

### Development Environment
- Default passwords are used (change for production!)
- CORS is permissive for local development
- Debug mode is enabled
- No HTTPS (use HTTP for local development)

### Environment Variables
Key settings in `.env`:
- `SECRET_KEY`: Application secret (change in production!)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- API keys for external services (optional)

## 🚀 Next Steps

After successful infrastructure setup:

1. **Verify All Services**: Ensure all health checks pass
2. **Check API Documentation**: Visit http://localhost:8000/docs
3. **Test Frontend**: Visit http://localhost:3000
4. **Configure API Keys**: Add real API keys to `.env` for external data
5. **Continue to Next Phase**: Proceed with backend development

## 📞 Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Review Docker logs: `./scripts/docker-dev.sh logs`
3. Verify environment variables in `.env`
4. Ensure Docker has enough resources (RAM/disk)
5. Check for port conflicts on your system

Happy coding! 🎉