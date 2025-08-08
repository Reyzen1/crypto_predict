# 🚀 Quick Start Guide

## ⚡ Get Started in 2 Minutes

### 1. Environment Setup
```bash
# Ensure you have your .env file configured
# DATABASE_URL=postgresql://postgres:admin123@localhost:5433/cryptopredict
# REDIS_URL=redis://127.0.0.1:6379/0
```

### 2. Switch to Local Development
```bash
chmod +x dev-mode-switcher.sh
./dev-mode-switcher.sh local
```

### 3. Start Services
```bash
# Terminal 1 - Backend
./start-backend-local.sh

# Terminal 2 - Frontend
./start-frontend-local.sh
```

### 4. Access Applications
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🔄 Switch Development Modes

### To Local Development
```bash
./dev-mode-switcher.sh local
```
**Uses**: PostgreSQL (localhost:5433) + Redis (127.0.0.1:6379)

### To Docker Development
```bash
./dev-mode-switcher.sh docker
```
**Uses**: Docker containers for all services

### Check Current Status
```bash
./dev-mode-switcher.sh status
```

---

## 💡 Key Features

### ✅ Automatic Configuration
- Reads from `.env` file automatically
- Smart backup and restore of configurations
- No manual file editing required

### ✅ Flexible Database Support
- Local PostgreSQL (any port)
- Docker PostgreSQL
- Auto-detects connection settings

### ✅ Environment Management
- One command to switch modes
- Preserves your API keys and settings
- Safe backup system

---

## 🔧 Prerequisites

### For Local Development
- PostgreSQL running on any port
- Redis running on default port (6379)
- Python virtual environment in `backend/venv/`
- Node.js dependencies in `frontend/node_modules/`

### For Docker Development
- Docker and Docker Compose installed

---

## 📋 Common Commands

```bash
# Check what's running
./dev-mode-switcher.sh status

# Switch modes
./dev-mode-switcher.sh local   # Local development
./dev-mode-switcher.sh docker  # Docker development

# Start development servers
./start-backend-local.sh       # Backend server
./start-frontend-local.sh      # Frontend server

# Database operations
createdb -h localhost -p 5433 -U postgres cryptopredict  # Create DB
psql -h localhost -p 5433 -U postgres cryptopredict      # Connect to DB
```

---

## 🆘 Troubleshooting

### Backend Won't Start
```bash
# Check database connection
pg_isready -h localhost -p 5433

# Check if virtual environment is active
echo $VIRTUAL_ENV

# Activate virtual environment manually
cd backend
source venv/Scripts/activate  # Windows Git Bash
source venv/bin/activate      # Linux/Mac
```

### Frontend Won't Start
```bash
# Check if Node.js dependencies are installed
cd frontend
ls node_modules/

# Install dependencies if missing
npm install
```

### Database Issues
```bash
# Create database if it doesn't exist
createdb -h localhost -p 5433 -U postgres cryptopredict

# Check if PostgreSQL is running on correct port
netstat -tulpn | grep 5433
```

### Switch Not Working
```bash
# Check current environment
cat .env | grep DATABASE_URL

# Manually restore backup if needed
cp .env.local.backup .env      # Restore local config
cp .env.docker.backup .env     # Restore Docker config
```

---

## 📖 Next Steps

1. **API Development**: Check http://localhost:8000/docs for API documentation
2. **Frontend Development**: Visit http://localhost:3000 to see the UI
3. **Database Management**: Tables are created automatically from models
4. **Configuration**: All settings are in `.env` file
5. **Advanced Setup**: See `docs/INFRASTRUCTURE_SETUP.md` for detailed information

---

## 💡 Pro Tips

- Use `./dev-mode-switcher.sh status` to debug configuration issues
- Your API keys and custom settings are preserved when switching modes
- Tables are created automatically - no manual migration needed for development
- Both startup scripts show detailed environment information when starting