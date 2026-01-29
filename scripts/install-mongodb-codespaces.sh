#!/bin/bash
# MongoDB Installation Script for Codespaces

echo "🔧 Installing MongoDB in Codespaces..."

# Update package list
sudo apt-get update

# Install MongoDB
sudo apt-get install -y mongodb

# Start MongoDB service
sudo systemctl start mongodb

# Enable MongoDB to start on boot (optional)
sudo systemctl enable mongodb

# Verify installation
echo "✅ MongoDB installed successfully!"
mongosh --eval "db.version()" --quiet

# Create database directory (if needed)
sudo mkdir -p /data/db
sudo chown -R $USER /data/db

echo ""
echo "🎉 MongoDB is ready!"
echo "Connection string: mongodb://localhost:27017"
echo ""
echo "To start MongoDB manually (if needed):"
echo "  sudo systemctl start mongodb"
echo ""
echo "To check MongoDB status:"
echo "  sudo systemctl status mongodb"
