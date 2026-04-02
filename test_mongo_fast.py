#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick MongoDB connection test with timeout"""

from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')

print(f"🔗 Testing MongoDB Connection (5s timeout)...")
print(f"URI: {MONGO_URI[:50]}...")
print(f"Database: {MONGODB_DB}\n")

try:
    # Connect to MongoDB with SHORT timeout
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,  # 5 second timeout
        connectTimeoutMS=5000,
        socketTimeoutMS=5000,
        retryWrites=True,
        ssl=True,
        tlsAllowInvalidCertificates=False
    )

    # Test connection with ping
    print("⏳ Pinging server...")
    client.admin.command('ping')
    print("✅ MongoDB CONNECTED!\n")

    # Get database
    db = client[MONGODB_DB]
    print(f"✅ Database '{MONGODB_DB}' available")

    # Quick collection count
    try:
        collections = db.list_collection_names()
        print(f"✅ Collections: {', '.join(collections) if collections else 'None'}")
    except:
        print("⚠️  Could not list collections")

    print("\n✅ CONNECTION SUCCESSFUL")
    sys.exit(0)

except Exception as e:
    print(f"\n❌ CONNECTION FAILED: {str(e)}")
    sys.exit(1)
