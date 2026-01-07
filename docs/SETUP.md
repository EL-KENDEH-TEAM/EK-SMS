# Local Development Setup

Complete guide to setting up EK-SMS on your local machine.

## Prerequisites

### Required Software

| Software       | Version | Download              |
| -------------- | ------- | --------------------- |
| Node.js        | 22+     | https://nodejs.org/   |
| Python         | 3.12+   | https://python.org/   |
| pnpm           | 9+      | `npm install -g pnpm` |
| Docker Desktop | Latest  | https://docker.com/   |
| Git            | Latest  | https://git-scm.com/  |

### Verify Installation

```bash
node --version    # Should show v22.x.x
python --version  # Should show Python 3.12.x
pnpm --version    # Should show 9.x.x
docker --version  # Should show Docker version xx.x.x
```

## Step-by-Step Setup

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/EK-SMS.git
cd EK-SMS
```

### 2. Install Node Dependencies

```bash
pnpm install
```

### 3. Set Up Python Environment

```bash
cd apps/api
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Deactivate when done
deactivate

cd ../..
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env.local
```

Edit `.env.local` with your local settings. The defaults work for most setups.

### 5. Start Docker Services

```bash
docker-compose up -d
```

Verify all containers are running:

```bash
docker-compose ps
```

You should see:

- eksms-postgres (port 5440)
- eksms-redis (port 6380)
- eksms-mailpit (port 8025)
- eksms-pgadmin (port 5050)

### 6. Run Database Migrations

```bash
cd apps/api
.venv\Scripts\activate
cd src
alembic -c ../alembic.ini upgrade head
deactivate
cd ../../..
```

### 7. Start Development Servers

```bash
pnpm dev
```

This starts both frontend and backend simultaneously.

## Verify Setup

### Check Services

| Service  | URL                        | Expected     |
| -------- | -------------------------- | ------------ |
| Frontend | http://localhost:3000      | Next.js page |
| API      | http://localhost:8002      | Welcome JSON |
| API Docs | http://localhost:8002/docs | Swagger UI   |
| Mailpit  | http://localhost:8025      | Email inbox  |
| pgAdmin  | http://localhost:5050      | Database GUI |

### Test Database Connection

Visit http://localhost:8002/debug/db

Expected response:

```json
{ "database": "connected", "result": 1 }
```

### Test Redis Connection

Visit http://localhost:8002/debug/redis

Expected response:

```json
{ "redis": "connected" }
```

## Common Issues

### Port Already in Use

If you see "port already allocated" errors:

1. Check what's using the port:

```bash
   netstat -ano | findstr :PORT_NUMBER
```

2. Either stop that service or update `.env.local` with different ports

Our default ports (to avoid conflicts):

- PostgreSQL: 5440 (not 5432)
- Redis: 6380 (not 6379)
- API: 8002 (not 8000)

### Docker Not Starting

1. Make sure Docker Desktop is running
2. Check Docker Desktop has enough resources allocated
3. Try restarting Docker Desktop

### Python Import Errors

Make sure you're in the virtual environment:

```bash
cd apps/api
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
```

### pnpm Install Fails

Clear cache and reinstall:

```bash
pnpm store prune
pnpm install
```

## Daily Workflow

### Starting Work

```bash
# 1. Start Docker (if not running)
docker-compose up -d

# 2. Start dev servers
pnpm dev
```

### Ending Work

```bash
# Stop dev servers
Ctrl+C

# Optionally stop Docker
docker-compose down
```

### Updating Dependencies

```bash
# Pull latest changes
git pull origin develop

# Install any new dependencies
pnpm install

# Update Python dependencies
cd apps/api
.venv\Scripts\activate
pip install -e ".[dev]"
deactivate
cd ../..

# Run any new migrations
cd apps/api/src
alembic -c ../alembic.ini upgrade head
cd ../../..
```

## IDE Setup

### VS Code (Recommended)

Install these extensions:

- Python
- Pylance
- ESLint
- Tailwind CSS IntelliSense
- Prettier

### PyCharm

1. Open `apps/api` as a project
2. Set Python interpreter to `.venv`
3. Enable Ruff integration

## Need Help?

1. Check the [Architecture Guide](./ARCHITECTURE.md)
2. Review the [Contributing Guide](../CONTRIBUTING.md)
3. Ask in the team chat
