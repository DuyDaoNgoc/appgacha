#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create admin account in MongoDB"""

from pymongo import MongoClient
from dotenv import load_dotenv
import os
import hashlib
from datetime import datetime

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')

print(f"🔗 Connecting to MongoDB...")

try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
        retryWrites=True,
        ssl=True,
        tlsAllowInvalidCertificates=False
    )
    client.admin.command('ping')
    db = client[MONGODB_DB]
    users = db['users']

    print("✅ Connected!")

    # Admin data
    username = 'admin'
    password = 'duypro0478'

    # Check if admin exists
    existing = users.find_one({'username': username})
    if existing:
        print(f"⚠️ User '{username}' already exists!")
        print(f"ID: {existing['_id']}")
    else:
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Create admin account
        admin_doc = {
            'username': username,
            'password': password_hash,
            'level': 1,
            'xu': 100000,
            'stars': 1000,
            'online': False,
            'created_at': datetime.utcnow().isoformat(),
            'is_admin': True
        }

        result = users.insert_one(admin_doc)
        print(f"✅ Admin account created!")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"ID: {result.inserted_id}")
        print(f"\n⚠️  Remember: Share admin password securely!")

except Exception as e:
    print(f"❌ Error: {str(e)}")
