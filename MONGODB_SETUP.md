# MongoDB Setup for Codespaces

## Option 1: MongoDB Atlas (Recommended - Free Cloud Database)

### Step 1: Create MongoDB Atlas Account
1. Visit: https://www.mongodb.com/cloud/atlas
2. Sign up for free account
3. Create a free cluster (M0 Sandbox - 512MB)

### Step 2: Get Connection String
1. Click "Connect" → "Drivers"
2. Choose "Python" and version "3.12 or later"
3. Copy connection string (looks like):
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

### Step 3: Update .env File
```bash
cd /workspaces/personal-agent/backend
nano .env
```

Add/Update:
```bash
MONGODB_CONNECTION_STRING=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE_NAME=agent_memory
```

### Step 4: Restart Backend
```bash
# Terminal 1
cd /workspaces/personal-agent/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Option 2: Local MongoDB in Codespaces

### Quick Setup (Run in Codespaces terminal)

```bash
# Install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb

# Start MongoDB service
sudo systemctl start mongodb

# Verify installation
mongosh --eval "db.version()"

# Keep MongoDB running
```

### Note: Local MongoDB Data Persistence
⚠️ **Warning**: Data in local MongoDB will be lost when Codespaces stops!
- Use this option for testing only
- Use MongoDB Atlas for production

---

## Verify MongoDB Connection

After setup, test the connection:

```python
# Test script
import motor.motor_asyncio

client = motor.motor_asyncio.AsyncIOMotorClient(
    "mongodb://localhost:27017"  # or your Atlas connection string
)

try:
    # Test connection
    await client.server_info()
    print("✅ MongoDB connected successfully!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

---

## Recommended: MongoDB Atlas

**Why use Atlas?**
- ✅ Data persists even when Codespaces stops
- ✅ Free tier: 512MB storage
- ✅ Easy to scale later
- ✅ Access from anywhere
- ✅ Automatic backups

**Free Tier Limits:**
- 512MB storage
- Shared RAM
- Sufficient for development and small projects
