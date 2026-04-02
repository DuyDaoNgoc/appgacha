#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test MongoDB connection"""

from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')

print(f"🔗 Testing MongoDB Connection...")
print(f"URI: {MONGO_URI[:50]}...")
print(f"Database: {MONGODB_DB}\n")

try:
    # Connect to MongoDB
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
        retryWrites=True,
        ssl=True,
        tlsAllowInvalidCertificates=False
    )

    # Test connection with ping
    client.admin.command('ping')
    print("✅ MongoDB connection successful!")

    # Get database
    db = client[MONGODB_DB]
    print(f"✅ Database '{MONGODB_DB}' accessed!")

    # List collections
    collections = db.list_collection_names()
    print(f"✅ Found {len(collections)} collections:")
    for col in collections:
        print(f"   - {col}")

    # Get database stats
    stats = db.command('dbStats')
    print(f"\n📊 Database Stats:")
    print(f"   - Data Size: {stats['dataSize'] / 1024 / 1024:.2f} MB")
    print(f"   - Collections: {stats['collections']}")
    print(f"   - Objects: {stats['objects']}")

except Exception as e:
    print(f"❌ MongoDB connection failed!")
    print(f"Error: {e}")
    print(f"\nTroubleshooting:")
    print(f"1. Check MongoDB URI is correct")
    print(f"2. Check internet connection")
    print(f"3. Check IP is whitelisted in MongoDB Atlas")
    print(f"4. Try with MongoDB Compass app")
