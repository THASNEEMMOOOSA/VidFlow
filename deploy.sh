# deploy.sh
#!/bin/bash

# Deployment script for VidFlow

echo "Starting VidFlow deployment..."

# Build Docker images
echo "Building Docker images..."
docker-compose build

# Run database migrations
echo "Running database migrations..."
docker-compose run --rm backend alembic upgrade head

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Run health checks
echo "Running health checks..."
curl -f http://localhost:8000/health || exit 1
curl -f http://localhost:3000 || exit 1

echo "Deployment completed successfully!"