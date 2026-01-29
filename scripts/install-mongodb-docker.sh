#!/bin/bash
# MongoDB Docker Setup for Codespaces

echo "🐳 Setting up MongoDB using Docker..."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not available in this Codespaces"
    echo ""
    echo "📝 Please use MongoDB Atlas instead:"
    echo "1. Visit: https://www.mongodb.com/cloud/atlas"
    echo "2. Create free account"
    echo "3. Create free M0 cluster"
    echo "4. Get connection string"
    echo "5. Update backend/.env:"
    echo "   MONGODB_CONNECTION_STRING=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"
    echo ""
    exit 1
fi

# Pull and run MongoDB in Docker
echo "📦 Pulling MongoDB Docker image..."
docker pull mongo:8.0

echo "🚀 Starting MongoDB container..."
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:8.0

# Wait for MongoDB to be ready
echo "⏳ Waiting for MongoDB to start..."
sleep 5

# Verify MongoDB is running
if docker ps | grep -q mongodb; then
    echo "✅ MongoDB is running in Docker!"
    echo ""
    echo "Connection string: mongodb://localhost:27017"
    echo ""
    echo "To stop MongoDB:"
    echo "  docker stop mongodb"
    echo ""
    echo "To start MongoDB again:"
    echo "  docker start mongodb"
    echo ""
    echo "To view MongoDB logs:"
    echo "  docker logs mongodb"
else
    echo "❌ Failed to start MongoDB"
    exit 1
fi
