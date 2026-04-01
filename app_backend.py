#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎮 Honkai Star Rail Gacha Game - Backend (MongoDB + Flask + Socket.io)
Full Online System with User Auth, Currency, Mailbox, Multiplayer
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from functools import wraps
from bson.objectid import ObjectId
import hashlib

# ============ Environment & Config ============
load_dotenv()
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb+srv://pracelJS:Duy04@duy04.wdkexkx.mongodb.net/gacha-game?retryWrites=true&w=majority')
JWT_SECRET = os.getenv('JWT_SECRET', 'gacha-game-secret-2024')
JWT_ALGORITHM = 'HS256'
GACHA_COST = 160  # Xu per roll

# ============ App Setup ============
app = Flask(__name__, static_url_path='', static_folder='project/www')
CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ============ MongoDB Connection ============
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ MongoDB Atlas connected!")
    db = client['gacha-game']
except Exception as e:
    print(f"❌ MongoDB failed: {e}")
    db = None

# ============ Collections ============
def get_collection(name):
    """Get MongoDB collection"""
    if db is None:
        print(f"⚠️  Database not connected, cannot access {name}")
        return None
    return db[name]

def get_users_collection():
    """Get users collection"""
    return get_collection('users')

def get_mailbox_collection():
    """Get mailbox collection"""
    return get_collection('mailbox')

def get_banners_collection():
    """Get banners collection"""
    return get_collection('banners')

def get_online_users():
    """Get online users collection"""
    return get_collection('online_users')

# ============ Authentication Helper ============
def hash_password(password):
    """Hash password with SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, password):
    """Verify password against stored hash"""
    return stored_hash == hash_password(password)

def create_token(user_id):
    """Create JWT token"""
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow() + timedelta(days=30),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload['user_id']
    except:
        return None

def token_required(f):
    """Decorator for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Missing token'}), 401

        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Invalid token'}), 401

        return f(user_id, *args, **kwargs)
    return decorated

# ============ API Routes - Auth ============
@app.route('/api/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        users = get_collection('users')
        if users.find_one({'username': username}):
            return jsonify({'error': 'Username already exists'}), 400

        user_doc = {
            'username': username,
            'password_hash': hash_password(password),
            'xu': 1000,  # Starting xu
            'stars': 0,  # Gacha star currency
            'created_at': datetime.utcnow(),
            'last_login': datetime.utcnow(),
            'online': False
        }
        result = users.insert_one(user_doc)
        token = create_token(result.inserted_id)

        # Initialize mailbox
        mailboxes = get_collection('mailboxes')
        mailboxes.insert_one({
            'user_id': result.inserted_id,
            'messages': []
        })

        return jsonify({
            'success': True,
            'token': token,
            'user_id': str(result.inserted_id),
            'username': username
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        users = get_collection('users')
        user = users.find_one({'username': username})

        if not user or not verify_password(user['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Update last login
        users.update_one({'_id': user['_id']}, {
            '$set': {'last_login': datetime.utcnow()}
        })

        token = create_token(user['_id'])

        return jsonify({
            'success': True,
            'token': token,
            'user_id': str(user['_id']),
            'username': username,
            'xu': user.get('xu', 0),
            'stars': user.get('stars', 0)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
@token_required
def logout(user_id):
    """Logout user - set offline status"""
    try:
        users = get_collection('users')
        users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'online': False}}
        )

        # Remove from online_users dict
        if user_id in online_users:
            del online_users[user_id]

        return jsonify({'success': True, 'message': 'Logged out'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/online', methods=['POST'])
@token_required
def set_user_online(user_id):
    """Set user online status"""
    try:
        users = get_collection('users')
        user = users.find_one({'_id': ObjectId(user_id)})

        if not user:
            return jsonify({'error': 'User not found'}), 404

        users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'online': True}}
        )

        # Add to online_users dict
        online_users[user_id] = {
            'username': user['username'],
            'timestamp': datetime.utcnow()
        }

        return jsonify({'success': True, 'message': 'User online'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ API Routes - User Data ============
@app.route('/api/user/profile', methods=['GET'])
@token_required
def get_profile(user_id):
    """Get user profile"""
    try:
        users = get_collection('users')
        user = users.find_one({'_id': ObjectId(user_id)})

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'username': user['username'],
            'xu': user.get('xu', 0),
            'stars': user.get('stars', 0),
            'online': user.get('online', False),
            'last_login': user.get('last_login', '').isoformat() if user.get('last_login') else ''
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/add-currency', methods=['POST'])
@token_required
def add_currency(user_id):
    """Add xu or stars to user (Admin only)"""
    try:
        data = request.json
        xu_amount = data.get('xu', 0)
        stars_amount = data.get('stars', 0)

        users = get_collection('users')
        result = users.update_one(
            {'_id': ObjectId(user_id)},
            {'$inc': {'xu': xu_amount, 'stars': stars_amount}}
        )

        if result.matched_count == 0:
            return jsonify({'error': 'User not found'}), 404

        updated_user = users.find_one({'_id': ObjectId(user_id)})
        return jsonify({
            'success': True,
            'xu': updated_user['xu'],
            'stars': updated_user['stars']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ API Routes - Gacha ============
@app.route('/api/gacha/roll', methods=['POST'])
@token_required
def gacha_roll(user_id):
    """Perform gacha roll"""
    try:
        data = request.json
        rolls = data.get('rolls', 1)  # 1 or 10

        users = get_collection('users')
        user = users.find_one({'_id': ObjectId(user_id)})

        total_cost = GACHA_COST * rolls
        if user.get('xu', 0) < total_cost:
            return jsonify({'error': f'Not enough xu. Need {total_cost}, have {user.get("xu", 0)}'}), 400

        # Deduct cost
        users.update_one(
            {'_id': ObjectId(user_id)},
            {'$inc': {'xu': -total_cost}}
        )

        # Generate results (mock)
        import random
        results = []
        rarities = ['R', 'SR', 'SSR', 'UR']
        characters = {
            'R': ['Arlan', 'Serval', 'Asta'],
            'SR': ['March 7th', 'Dan Heng', 'Blade'],
            'SSR': ['Jingliu', 'Kafka'],
            'UR': ['Acheron', 'Sparkle']
        }

        for _ in range(rolls):
            rarity = random.choice(rarities)
            character = random.choice(characters[rarity])
            results.append({'character': character, 'rarity': rarity})

        # Record in history
        history = get_collection('history')
        history.insert_one({
            'user_id': ObjectId(user_id),
            'rolls': rolls,
            'results': results,
            'timestamp': datetime.utcnow()
        })

        return jsonify({
            'success': True,
            'results': results,
            'xu_remaining': user.get('xu', 0) - total_cost
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ API Routes - Mailbox ============
@app.route('/api/mailbox/messages', methods=['GET'])
@token_required
def get_mailbox(user_id):
    """Get user mailbox messages"""
    try:
        mailboxes = get_collection('mailboxes')
        mailbox = mailboxes.find_one({'user_id': ObjectId(user_id)})

        if not mailbox:
            return jsonify({'messages': []}), 200

        return jsonify({
            'messages': [
                {
                    'id': str(m['_id']),
                    'from': m.get('from', 'Admin'),
                    'subject': m.get('subject', ''),
                    'content': m.get('content', ''),
                    'xu': m.get('xu', 0),
                    'stars': m.get('stars', 0),
                    'items': m.get('items', []),
                    'read': m.get('read', False),
                    'timestamp': m.get('timestamp', '').isoformat() if m.get('timestamp') else ''
                } for m in mailbox.get('messages', [])
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mailbox/claim/<message_id>', methods=['POST'])
@token_required
def claim_reward(user_id, message_id):
    """Claim reward from mailbox message"""
    try:
        mailboxes = get_collection('mailboxes')
        users = get_collection('users')

        mailbox = mailboxes.find_one({'user_id': ObjectId(user_id)})
        if not mailbox:
            return jsonify({'error': 'Mailbox not found'}), 404

        # Find message
        message = None
        for msg in mailbox.get('messages', []):
            if str(msg['_id']) == message_id:
                message = msg
                break

        if not message:
            return jsonify({'error': 'Message not found'}), 404

        if message.get('claimed', False):
            return jsonify({'error': 'Already claimed'}), 400

        # Add rewards to user
        xu_reward = message.get('xu', 0)
        stars_reward = message.get('stars', 0)

        users.update_one(
            {'_id': ObjectId(user_id)},
            {'$inc': {'xu': xu_reward, 'stars': stars_reward}}
        )

        # Mark as claimed
        mailboxes.update_one(
            {'user_id': ObjectId(user_id), 'messages._id': message['_id']},
            {'$set': {'messages.$.claimed': True, 'messages.$.read': True}}
        )

        return jsonify({
            'success': True,
            'xu_gained': xu_reward,
            'stars_gained': stars_reward
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ Admin Routes ============
@app.route('/api/admin/send-message', methods=['POST'])
def admin_send_message():
    """Admin send message to user (no auth for now)"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        subject = data.get('subject', '')
        content = data.get('content', '')
        xu = data.get('xu', 0)
        stars = data.get('stars', 0)

        users = get_collection('users')
        user = users.find_one({'username': username})

        if not user:
            return jsonify({'error': 'User not found'}), 404

        mailboxes = get_collection('mailboxes')
        message = {
            '_id': ObjectId(),
            'from': 'Admin',
            'subject': subject,
            'content': content,
            'xu': xu,
            'stars': stars,
            'items': [],
            'read': False,
            'claimed': False,
            'timestamp': datetime.utcnow()
        }

        mailboxes.update_one(
            {'user_id': user['_id']},
            {'$push': {'messages': message}},
            upsert=True
        )

        return jsonify({'success': True, 'message_id': str(message['_id'])}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ Socket.io - Online Status ============
online_users = {}  # {user_id: {'username': '', 'sid': ''}}

@socketio.on('user_online')
def handle_user_online(data):
    """User goes online"""
    try:
        user_id = data.get('user_id')
        username = data.get('username')

        if user_id and username:
            online_users[user_id] = {
                'username': username,
                'sid': request.sid,
                'timestamp': datetime.utcnow()
            }

            # Update database
            users = get_collection('users')
            users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'online': True}}
            )

            # Broadcast online users list
            emit('online_users_list', {
                'users': [
                    {'user_id': uid, 'username': v['username']}
                    for uid, v in online_users.items()
                ]
            }, broadcast=True)

            print(f"✅ {username} online")
    except Exception as e:
        print(f"❌ Error: {e}")

@socketio.on('user_offline')
def handle_user_offline(data):
    """User goes offline"""
    try:
        user_id = data.get('user_id')

        if user_id in online_users:
            username = online_users[user_id]['username']
            del online_users[user_id]

            # Update database
            users = get_collection('users')
            users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'online': False}}
            )

            # Broadcast
            emit('online_users_list', {
                'users': [
                    {'user_id': uid, 'username': v['username']}
                    for uid, v in online_users.items()
                ]
            }, broadcast=True)

            print(f"❌ {username} offline")
    except Exception as e:
        print(f"❌ Error: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle disconnection"""
    for user_id in list(online_users.keys()):
        if online_users[user_id]['sid'] == request.sid:
            del online_users[user_id]
            break

@app.route('/api/online-users', methods=['GET'])
def get_online_users():
    """Get list of online users"""
    return jsonify({
        'online_users': [
            {'user_id': uid, 'username': v['username']}
            for uid, v in online_users.items()
        ]
    }), 200

# ============ Static Files ============
@app.route('/')
def index():
    """Serve home.html"""
    return send_from_directory('project/www', 'home.html')

@app.route('/game')
def game():
    """Serve game page"""
    return send_from_directory('project/www', 'index.html')

@app.route('/admin')
def admin():
    """Serve admin page"""
    return send_from_directory('project/www', 'admin.html')

# ============ Health Check ============
@app.route('/api/health', methods=['GET'])
def health():
    """API health check"""
    return jsonify({
        'status': 'ok',
        'mongo': 'connected' if db else 'disconnected',
        'online_users': len(online_users)
    }), 200



# ============ Helper Functions ============
def generate_token(user_id, username):
    """Generate JWT token"""
    payload = {
        'user_id': str(user_id),
        'username': username,
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Missing token'}), 401

        token = token.replace('Bearer ', '')
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401

        request.user = payload
        return f(*args, **kwargs)
    return decorated

# ============ Routes ============

# Serve static files
@app.route('/')
def index():
    return send_from_directory('project/www', 'home.html')

@app.route('/gacha')
def gacha_page():
    return send_from_directory('project/www', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('project/www', 'admin.html')

# ============ Authentication APIs ============

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user"""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    users = get_users_collection()

    # Check if user exists
    if users.find_one({'username': username}):
        return jsonify({'error': 'Username already exists'}), 400

    # Create user
    user = {
        'username': username,
        'password': password,  # ⚠️ In production, use bcrypt!
        'created_at': datetime.utcnow(),
        'lastLogin': None,
        'xu': 1000,  # Starting currency
        'stars': 5,  # Starting stars
        'mailbox': [],  # Unread items
        'banners': [],  # Owned banners
        'history': []  # Roll history
    }

    result = users.insert_one(user)
    user['_id'] = str(result.inserted_id)

    token = generate_token(user['_id'], username)

    return jsonify({
        'message': 'User created',
        'user_id': str(result.inserted_id),
        'token': token,
        'xu': 1000,
        'stars': 5
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    users = get_users_collection()
    user = users.find_one({'username': username})

    if not user or user['password'] != password:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Update last login
    users.update_one({'_id': user['_id']}, {
        '$set': {'lastLogin': datetime.utcnow()}
    })

    token = generate_token(str(user['_id']), username)

    return jsonify({
        'message': 'Login successful',
        'user_id': str(user['_id']),
        'token': token,
        'xu': user.get('xu', 0),
        'stars': user.get('stars', 0),
        'username': username
    }), 200

@app.route('/api/user/profile', methods=['GET'])
@token_required
def get_profile():
    """Get user profile"""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500

    users = get_users_collection()
    user = users.find_one({'_id': ObjectId(request.user['user_id'])})

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'username': user['username'],
        'xu': user.get('xu', 0),
        'stars': user.get('stars', 0),
        'created_at': user['created_at'].isoformat(),
        'lastLogin': user['lastLogin'].isoformat() if user['lastLogin'] else None
    }), 200

# ============ Gacha APIs ============

@app.route('/api/gacha/roll', methods=['POST'])
@token_required
def gacha_roll():
    """Roll gacha - costs 160 xu per roll"""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500

    data = request.get_json()
    count = data.get('count', 1)  # 1 or 10

    if count not in [1, 10]:
        return jsonify({'error': 'Count must be 1 or 10'}), 400

    users = get_users_collection()
    user = users.find_one({'_id': ObjectId(request.user['user_id'])})

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Check currency
    cost = GACHA_COST * count
    if user.get('xu', 0) < cost:
        return jsonify({'error': 'Insufficient xu'}), 400

    # Gacha items (rarity rates for HSR)
    items = [
        {'name': '3-Star', 'rarity': 3, 'rate': 0.85, 'emoji': '⭐'},
        {'name': '4-Star', 'rarity': 4, 'rate': 0.10, 'emoji': '🌟'},
        {'name': '5-Star', 'rarity': 5, 'rate': 0.03, 'emoji': '👑'},
        {'name': 'Fail', 'rarity': 0, 'rate': 0.02, 'emoji': '❌'},
    ]

    # Perform rolls
    results = []
    import random

    for _ in range(count):
        rand = random.random()
        cumulative = 0

        for item in items:
            cumulative += item['rate']
            if rand <= cumulative:
                results.append({
                    'name': item['name'],
                    'rarity': item['rarity'],
                    'emoji': item['emoji'],
                    'timestamp': datetime.utcnow().isoformat()
                })
                break

    # Deduct currency
    users.update_one({'_id': user['_id']}, {
        '$inc': {'xu': -cost},
        '$push': {
            'history': {
                'timestamp': datetime.utcnow(),
                'count': count,
                'cost': cost,
                'results': results
            }
        }
    })

    return jsonify({
        'results': results,
        'cost': cost,
        'remaining_xu': user.get('xu', 0) - cost
    }), 200

# ============ Mailbox APIs ============

@app.route('/api/mailbox', methods=['GET'])
@token_required
def get_mailbox():
    """Get user mailbox"""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500

    mailbox = get_mailbox_collection()
    user_mails = list(mailbox.find({
        'recipient': request.user['username'],
        'read': False
    }))

    for mail in user_mails:
        mail['_id'] = str(mail['_id'])

    return jsonify(user_mails), 200

@app.route('/api/mailbox/<mail_id>/claim', methods=['POST'])
@token_required
def claim_mail(mail_id):
    """Claim mailbox reward"""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500

    mailbox = get_mailbox_collection()
    users = get_users_collection()

    mail = mailbox.find_one({'_id': ObjectId(mail_id)})
    if not mail:
        return jsonify({'error': 'Mail not found'}), 404

    # Mark as read
    mailbox.update_one({'_id': ObjectId(mail_id)}, {
        '$set': {'read': True, 'claimed_at': datetime.utcnow()}
    })

    # Add rewards to user
    if mail.get('xu'):
        users.update_one(
            {'username': request.user['username']},
            {'$inc': {'xu': mail['xu']}}
        )

    if mail.get('stars'):
        users.update_one(
            {'username': request.user['username']},
            {'$inc': {'stars': mail['stars']}}
        )

    return jsonify({'message': 'Reward claimed'}), 200

@app.route('/api/admin/mailbox/send', methods=['POST'])
def send_mail():
    """Admin: Send mail to user"""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500

    # In production, check admin role!
    data = request.get_json()
    username = data.get('username')
    message = data.get('message')
    xu = data.get('xu', 0)
    stars = data.get('stars', 0)

    if not username or not message:
        return jsonify({'error': 'Missing fields'}), 400

    mailbox = get_mailbox_collection()
    mail = {
        'recipient': username,
        'sender': 'admin',
        'message': message,
        'xu': xu,
        'stars': stars,
        'read': False,
        'created_at': datetime.utcnow(),
        'claimed_at': None
    }

    result = mailbox.insert_one(mail)

    return jsonify({
        'message': 'Mail sent',
        'mail_id': str(result.inserted_id)
    }), 201

# ============ Online Status (Socket.io) ============

online_users = {}  # {username: socketId}

@socketio.on('connect')
def on_connect():
    """User connected"""
    print(f"✅ User connected: {request.sid}")

@socketio.on('login')
def on_login(data):
    """User logged in"""
    username = data.get('username')
    user_id = data.get('user_id')

    if not db:
        emit('login_response', {'status': 'offline'})
        return

    online_users[username] = request.sid

    # Save to database
    online = get_online_users()
    online.update_one(
        {'username': username},
        {
            '$set': {
                'user_id': user_id,
                'socket_id': request.sid,
                'online': True,
                'last_seen': datetime.utcnow()
            }
        },
        upsert=True
    )

    # Broadcast online status
    socketio.emit('user_online', {
        'username': username,
        'timestamp': datetime.utcnow().isoformat()
    }, broadcast=True)

    emit('login_response', {'status': 'online'})

@socketio.on('disconnect')
def on_disconnect():
    """User disconnected"""
    for username, sid in list(online_users.items()):
        if sid == request.sid:
            del online_users[username]

            if db:
                online = get_online_users()
                online.update_one(
                    {'username': username},
                    {'$set': {'online': False, 'last_seen': datetime.utcnow()}}
                )

            socketio.emit('user_offline', {
                'username': username,
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True)
            break

@app.route('/api/online-users', methods=['GET'])
def get_online_list():
    """Get list of online users"""
    return jsonify({
        'online': list(online_users.keys()),
        'count': len(online_users)
    }), 200

# ============ Error Handling ============

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# ============ Run ============

if __name__ == '__main__':
    print("""
    🎮 Honkai Star Rail Gacha Game Backend
    ✨ MongoDB + Socket.io + Flask

    📝 Setup:
    1. Create .env file with MONGODB_URI
    2. Run: python app_backend.py
    """)

    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
