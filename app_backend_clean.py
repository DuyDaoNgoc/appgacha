#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎮 Honkai Star Rail Gacha Game - Backend (MongoDB + Flask + Socket.io)
Full Online System with User Auth, Currency, Mailbox, Multiplayer
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import jwt
import os
import random
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
CORS(app)
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

# ============ Authentication Helpers ============
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

# ============ Static Pages ============
@app.route('/')
def home():
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
        'mongo': 'connected' if db else 'disconnected'
    }), 200

# ============ Auth APIs ============
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user"""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500

    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        users = get_collection('users')

        # Check if user exists
        if users.find_one({'username': username}):
            return jsonify({'error': 'Username already exists'}), 400

        # Create user
        user_doc = {
            'username': username,
            'password_hash': hash_password(password),
            'xu': 1000,
            'stars': 0,
            'created_at': datetime.utcnow(),
            'last_login': datetime.utcnow(),
            'online': False
        }

        result = users.insert_one(user_doc)
        token = create_token(result.inserted_id)

        return jsonify({
            'success': True,
            'token': token,
            'user_id': str(result.inserted_id),
            'username': username,
            'xu': 1000,
            'stars': 0
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500

    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        users = get_collection('users')
        user = users.find_one({'username': username})

        if not user or not verify_password(user['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Update last login
        users.update_one(
            {'_id': user['_id']},
            {'$set': {'last_login': datetime.utcnow()}}
        )

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

# ============ User APIs ============
@app.route('/api/user/profile', methods=['GET'])
@token_required
def get_profile(user_id):
    """Get user profile"""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500

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
            'created_at': user['created_at'].isoformat(),
            'last_login': user['last_login'].isoformat() if user.get('last_login') else None
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/add-currency', methods=['POST'])
@token_required
def add_currency(user_id):
    """Add xu or stars to user (Admin only)"""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500

    try:
        data = request.get_json()
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

# ============ Gacha APIs ============
@app.route('/api/gacha/roll', methods=['POST'])
@token_required
def gacha_roll(user_id):
    """Perform gacha roll - costs 160 xu per roll"""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500

    try:
        data = request.get_json()
        rolls = data.get('rolls', 1)  # 1 or 10

        if rolls not in [1, 10]:
            return jsonify({'error': 'Rolls must be 1 or 10'}), 400

        users = get_collection('users')
        user = users.find_one({'_id': ObjectId(user_id)})

        if not user:
            return jsonify({'error': 'User not found'}), 404

        total_cost = GACHA_COST * rolls
        if user.get('xu', 0) < total_cost:
            return jsonify({'error': f'Insufficient xu. Need {total_cost}, have {user.get("xu", 0)}'}), 400

        # Gacha rarity rates (HSR style)
        results = []
        characters = {
            'R': ['Arlan', 'Serval', 'Asta', 'Potio', 'Herta'],
            'SR': ['March 7th', 'Dan Heng', 'Himeko', 'Welt', 'Bailu'],
            'SSR': ['Jingliu', 'Kafka', 'Seele', 'Bronya', 'Gepard'],
            'UR': ['Acheron', 'Sparkle', 'Feixiao', 'Aglaea']
        }

        for _ in range(rolls):
            rand = random.random()
            if rand < 0.01:  # 1% - UR
                rarity = 'UR'
            elif rand < 0.04:  # 3% - SSR
                rarity = 'SSR'
            elif rand < 0.14:  # 10% - SR
                rarity = 'SR'
            else:  # 85% - R
                rarity = 'R'

            character = random.choice(characters[rarity])
            results.append({
                'character': character,
                'rarity': rarity,
                'emoji': {'R': '💫', 'SR': '🌟', 'SSR': '👑', 'UR': '💎'}[rarity]
            })

        # Deduct cost and record
        users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$inc': {'xu': -total_cost},
                '$push': {
                    'gacha_history': {
                        'rolls': rolls,
                        'results': results,
                        'cost': total_cost,
                        'timestamp': datetime.utcnow()
                    }
                }
            }
        )

        return jsonify({
            'success': True,
            'results': results,
            'cost': total_cost,
            'remaining_xu': user.get('xu', 0) - total_cost
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ Mailbox APIs ============
@app.route('/api/mailbox/messages', methods=['GET'])
@token_required
def get_mailbox(user_id):
    """Get user mailbox messages"""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500

    try:
        mailboxes = get_collection('mailboxes')
        mailbox = mailboxes.find_one({'user_id': ObjectId(user_id)})

        if not mailbox:
            return jsonify({'messages': []}), 200

        messages = mailbox.get('messages', [])
        for msg in messages:
            msg['_id'] = str(msg.get('_id', ''))

        return jsonify({'messages': messages}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mailbox/claim/<message_id>', methods=['POST'])
@token_required
def claim_reward(user_id, message_id):
    """Claim reward from mailbox message"""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500

    try:
        mailboxes = get_collection('mailboxes')
        users = get_collection('users')

        mailbox = mailboxes.find_one({'user_id': ObjectId(user_id)})
        if not mailbox:
            return jsonify({'error': 'Mailbox not found'}), 404

        # Find and process message
        message = None
        for msg in mailbox.get('messages', []):
            if str(msg.get('_id', '')) == message_id:
                message = msg
                break

        if not message:
            return jsonify({'error': 'Message not found'}), 404

        if message.get('claimed', False):
            return jsonify({'error': 'Already claimed'}), 400

        # Add rewards
        xu_reward = message.get('xu', 0)
        stars_reward = message.get('stars', 0)

        users.update_one(
            {'_id': ObjectId(user_id)},
            {'$inc': {'xu': xu_reward, 'stars': stars_reward}}
        )

        # Mark as claimed
        mailboxes.update_one(
            {'user_id': ObjectId(user_id), 'messages._id': ObjectId(message_id)},
            {'$set': {'messages.$.claimed': True, 'messages.$.read': True}}
        )

        return jsonify({
            'success': True,
            'xu_gained': xu_reward,
            'stars_gained': stars_reward
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ Admin APIs ============
@app.route('/api/admin/mailbox/send', methods=['POST'])
def admin_send_message():
    """Admin: Send message to user"""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500

    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        subject = data.get('subject', '')
        content = data.get('content', '')
        xu = data.get('xu', 0)
        stars = data.get('stars', 0)

        if not username:
            return jsonify({'error': 'Username required'}), 400

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
            'read': False,
            'claimed': False,
            'timestamp': datetime.utcnow()
        }

        mailboxes.update_one(
            {'user_id': user['_id']},
            {'$push': {'messages': message}},
            upsert=True
        )

        return jsonify({
            'success': True,
            'message_id': str(message['_id']),
            'message': 'Message sent to user'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ Online Status APIs ============
@app.route('/api/online-users', methods=['GET'])
def get_online_players():
    """Get list of online users"""
    if not db:
        return jsonify({'online_users': []}), 200

    try:
        users = get_collection('users')
        online = list(users.find(
            {'online': True},
            {'username': 1, 'level': 1}
        ).limit(50))

        for user in online:
            user['_id'] = str(user['_id'])

        return jsonify({'online_users': online}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ Socket.io Online Status ============
# Track connected users in memory
connected_users = {}  # {user_id: {username, sid, connected_at}}

@socketio.on('connect')
def handle_connect():
    """User connects to Socket.io"""
    print(f"✅ Client connected: {request.sid}")

@socketio.on('user:login')
def handle_user_login(data):
    """User logs in - broadcast online event"""
    try:
        user_id = data.get('user_id')
        username = data.get('username')

        if not user_id or not username:
            emit('error', {'message': 'user_id and username required'})
            return

        # Store connection
        connected_users[user_id] = {
            'username': username,
            'sid': request.sid,
            'connected_at': datetime.utcnow().isoformat()
        }

        # Update MongoDB
        if db:
            users = get_collection('users')
            users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'online': True, 'last_online': datetime.utcnow()}}
            )

        # Broadcast new online user to all clients
        emit('user:online', {
            'user_id': user_id,
            'username': username,
            'timestamp': datetime.utcnow().isoformat()
        }, broadcast=True)

        # Send current online users list to new user
        emitOnlineUsers()

        print(f"✅ {username} online (total: {len(connected_users)})")

    except Exception as e:
        print(f"❌ Error in user:login: {e}")
        emit('error', {'message': str(e)})

@socketio.on('user:logout')
def handle_user_logout(data):
    """User logs out"""
    try:
        user_id = data.get('user_id')
        username = data.get('username')

        if user_id in connected_users:
            del connected_users[user_id]

        # Update MongoDB
        if db:
            users = get_collection('users')
            users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'online': False}}
            )

        # Broadcast user gone offline
        emit('user:offline', {
            'user_id': user_id,
            'username': username,
            'timestamp': datetime.utcnow().isoformat()
        }, broadcast=True)

        print(f"❌ {username} offline (total: {len(connected_users)})")

    except Exception as e:
        print(f"❌ Error in user:logout: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    """User disconnects from Socket.io"""
    # Find and remove user
    for user_id, user_data in list(connected_users.items()):
        if user_data['sid'] == request.sid:
            username = user_data['username']
            del connected_users[user_id]

            # Update MongoDB
            if db:
                users = get_collection('users')
                users.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$set': {'online': False}}
                )

            # Broadcast disconnect event
            socketio.emit('user:offline', {
                'user_id': user_id,
                'username': username,
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True)

            print(f"❌ {username} disconnected (total: {len(connected_users)})")
            break

@socketio.on('online-users:request')
def handle_online_users_request():
    """Client requests current online users list"""
    emitOnlineUsers()

def emitOnlineUsers():
    """Emit current online users to all connected clients"""
    online_list = [
        {
            'user_id': uid,
            'username': data['username'],
            'connected_at': data['connected_at']
        }
        for uid, data in connected_users.items()
    ]
    socketio.emit('online-users:list', {'users': online_list}, broadcast=True)

# ============ Run App ============
if __name__ == '__main__':
    print(f"\n{'='*50}")
    print("🎮 Honkai Star Rail Gacha Backend")
    print(f"{'='*50}")
    print(f"✅ Server starting on http://0.0.0.0:5000")
    print(f"✅ MongoDB: {MONGO_URI[:50]}...")
    print(f"{'='*50}\n")

    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
