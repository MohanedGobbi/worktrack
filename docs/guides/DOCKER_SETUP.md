# Docker & Docker Compose Setup for WorkTrack Pro

## Prerequisites
- Docker
- Docker Compose

## Quick Start with Docker

### 1. Build and Start Services
```bash
docker-compose up -d --build
```

This will start:
- PostgreSQL database on port 5432
- Redis cache on port 6379
- Django application on port 8000
- Celery worker
- Celery Beat (scheduled tasks)

### 2. Run Initial Migrations
```bash
docker-compose exec web python manage.py migrate
```

### 3. Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### 4. Access Application
- **API**: http://localhost:8000/api
- **Admin**: http://localhost:8000/admin
- **Database**: localhost:5432 (psql worktrack_pro -U postgres)
- **Redis**: localhost:6379

## Docker Commands

### View Logs
```bash
docker-compose logs -f web          # Django logs
docker-compose logs -f celery       # Celery logs
docker-compose logs -f db           # Database logs
```

### Run Management Commands
```bash
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py dumpdata > backup.json
docker-compose exec web python manage.py loaddata backup.json
```

### Stop Services
```bash
docker-compose down                 # Stop all services
docker-compose down -v              # Stop and remove volumes
```

### Rebuild After Code Changes
```bash
docker-compose build --no-cache
docker-compose up -d --force-recreate
```

### Database Connection
```bash
# From host machine
psql -h localhost -U postgres -d worktrack_pro

# From container
docker-compose exec db psql -U postgres -d worktrack_pro
```

### Access Redis
```bash
docker-compose exec redis redis-cli
> ping
PONG
```

## Production Deployment

### 1. Update Environment Variables
```bash
cp .env.example .env
# Edit .env with production values:
# - DEBUG=False
# - ALLOWED_HOSTS=yourdomain.com
# - Secure SECRET_KEY
# - Real database credentials
# - Real email settings
```

### 2. Use Docker for Production
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. Setup Nginx Reverse Proxy
```nginx
upstream worktrack {
    server web:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://worktrack;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /app/staticfiles/;
    }
    
    location /media/ {
        alias /app/media/;
    }
}
```

## Troubleshooting Docker

### Port Already in Use
```bash
docker-compose down
# OR use different port mapping in docker-compose.yml
```

### Database Connection Failed
```bash
# Ensure db service is healthy
docker-compose ps

# Check logs
docker-compose logs db
```

### Migrations Failed
```bash
# Reset database (development only!)
docker-compose exec db dropdb -U postgres worktrack_pro
docker-compose exec db createdb -U postgres worktrack_pro
docker-compose exec web python manage.py migrate
```

### Clear Cache
```bash
docker-compose exec redis redis-cli
> FLUSHALL
```

### Rebuild Everything
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

## Development Workflow

### 1. Make Code Changes
Changes are automatically reflected due to volume mounts.

### 2. Install New Dependencies
```bash
# Add to requirements.txt
pip install new-package
pip freeze > requirements.txt

# Rebuild Docker image
docker-compose build web
docker-compose up -d
```

### 3. Create Migrations
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### 4. Test Changes
```bash
# Run tests in container
docker-compose exec web python manage.py test

# Or for specific app
docker-compose exec web python manage.py test users
```

## Docker Networking

Services communicate via service names:
- `db` - PostgreSQL
- `redis` - Redis cache
- `web` - Django app
- `celery` - Celery worker
- `celery-beat` - Scheduled tasks

From Django settings perspective:
- Database host: `db`
- Redis URL: `redis://redis:6379/0`

## Performance Tips

1. **Use volume mounts wisely** - Avoid large directories
2. **Set resource limits** in docker-compose.yml
3. **Use .dockerignore** to exclude unnecessary files
4. **Optimize base images** - Use alpine variants
5. **Layer caching** - Put stable dependencies early in Dockerfile

## Monitoring

### CPU and Memory Usage
```bash
docker stats worktrack_web

# Output shows:
# CONTAINER             CPU %     MEM USAGE / LIMIT
# worktrack_web         0.50%     125MB / 2GB
```

### Health Checks
```bash
# View health status
docker-compose ps

# STATUS shows "healthy" or "unhealthy"
```

## Backup & Restore

### Backup Database
```bash
docker-compose exec db pg_dump -U postgres worktrack_pro > backup.sql
```

### Restore Database
```bash
docker-compose exec db psql -U postgres worktrack_pro < backup.sql
```

### Backup Uploaded Files
```bash
docker cp worktrack_web:/app/media ./media-backup
```
