#!/bin/bash
# Quick Start Script for Personal Agent in Codespaces

echo "🚀 Setting up Personal Agent in Codespaces..."
echo ""

# Step 1: Setup MongoDB using Docker
echo "📦 Setting up MongoDB..."
bash scripts/install-mongodb-docker.sh

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  MongoDB Docker setup failed"
    echo "Please use MongoDB Atlas instead (see MONGODB_SETUP.md)"
    echo ""
fi

# Step 2: Update backend dependencies
echo "📦 Installing Python dependencies..."
cd backend
source venv/bin/activate
pip install motor pymongo -q

# Step 3: Update .env if needed
if ! grep -q "MONGODB_CONNECTION_STRING" .env; then
    echo ""
    echo "📝 Adding MongoDB configuration to .env..."
    echo "" >> .env
    echo "# MongoDB" >> .env
    echo "MONGODB_CONNECTION_STRING=mongodb://localhost:27017" >> .env
    echo "MONGODB_DATABASE_NAME=agent_memory" >> .env
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Start backend (Terminal 1):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "2. Start frontend (Terminal 2):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Open the port 5173 link in Codespaces!"
echo ""
echo "💡 If MongoDB failed to start, use MongoDB Atlas:"
echo "   See: MONGODB_SETUP.md"
echo ""
echo "🍵 Happy coding!"
