#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import hashlib
import sqlite3
import time
import base64
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session, send_file, send_from_directory
from flask_cors import CORS
import secrets
import uuid

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app, supports_credentials=True)

# データベース初期化
def init_database():
    os.makedirs('data', exist_ok=True)
    os.makedirs('files', exist_ok=True)
    os.makedirs('files/uploads', exist_ok=True)
    os.makedirs('files/avatars', exist_ok=True)
    os.makedirs('files/whiteboards', exist_ok=True)
    
    conn = sqlite3.connect('data/circle_platform.db')
    cursor = conn.cursor()
    
    # ユーザーテーブル（拡張）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nickname TEXT,
            email TEXT,
            admission_year INTEGER,
            graduation_year INTEGER,
            major TEXT,
            student_id TEXT,
            bio TEXT,
            avatar TEXT,
            ui_scale TEXT DEFAULT 'medium',
            theme TEXT DEFAULT 'dark',
            language TEXT DEFAULT 'ja',
            timezone TEXT DEFAULT 'Asia/Tokyo',
            notification_settings TEXT DEFAULT '{}',
            privacy_settings TEXT DEFAULT '{}',
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 既存データベースとの互換性確保: 古いスキーマに対して必要なカラムを追加
    try:
        cursor.execute("PRAGMA table_info(users)")
        cols = [row[1] for row in cursor.fetchall()]
        if 'last_login' not in cols:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
            except Exception:
                # SQLite の古いバージョンや予期せぬエラーは無視して続行
                pass
    except Exception:
        # PRAGMA がサポートされていない環境でも無視
        pass
    
    # サーバー（サークル）テーブル（拡張）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            icon TEXT NOT NULL,
            banner TEXT,
            owner_id INTEGER,
            is_public BOOLEAN DEFAULT 0,
            invite_code TEXT UNIQUE,
            max_members INTEGER DEFAULT 100,
            settings TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users (id)
        )
    ''')

    # 既存データベースとの互換性確保: servers テーブルに必要なカラムを追加
    try:
        cursor.execute("PRAGMA table_info(servers)")
        cols = [row[1] for row in cursor.fetchall()]
        server_alters = [
            ("description", "TEXT", "NULL"),
            ("banner", "TEXT", "NULL"),
            ("is_public", "BOOLEAN", "0"),
            ("invite_code", "TEXT", "NULL"),
            ("max_members", "INTEGER", "100"),
            ("settings", "TEXT", "'{}'"),
            ("updated_at", "TIMESTAMP", "CURRENT_TIMESTAMP")
        ]
        for name, typ, default in server_alters:
            if name not in cols:
                try:
                    cursor.execute(f"ALTER TABLE servers ADD COLUMN {name} {typ} DEFAULT {default}")
                except Exception:
                    # ALTER が失敗しても続行（SQLite の制約など）
                    pass
    except Exception:
        pass
    
    # サーバーメンバーシップテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS server_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT DEFAULT 'member',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            invited_by INTEGER,
            permissions TEXT DEFAULT '{}',
            UNIQUE(server_id, user_id),
            FOREIGN KEY (server_id) REFERENCES servers (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (invited_by) REFERENCES users (id)
        )
    ''')
    
    # サーバー招待テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS server_invites (
            id TEXT PRIMARY KEY,
            server_id TEXT NOT NULL,
            inviter_id INTEGER NOT NULL,
            invitee_email TEXT,
            invitee_username TEXT,
            invite_code TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP,
            used_at TIMESTAMP,
            used_by INTEGER,
            max_uses INTEGER DEFAULT 1,
            current_uses INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (server_id) REFERENCES servers (id),
            FOREIGN KEY (inviter_id) REFERENCES users (id),
            FOREIGN KEY (used_by) REFERENCES users (id)
        )
    ''')
    
    # パスワード復旧テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_recovery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            recovery_partner_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            request_type TEXT DEFAULT 'reset',
            initiated_by INTEGER NOT NULL,
            recovery_token TEXT UNIQUE,
            expires_at TIMESTAMP,
            approved_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, recovery_partner_id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (recovery_partner_id) REFERENCES users (id),
            FOREIGN KEY (initiated_by) REFERENCES users (id)
        )
    ''')
    
    # ファイルテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type TEXT NOT NULL,
            upload_by INTEGER NOT NULL,
            server_id TEXT,
            feature_id TEXT,
            is_public BOOLEAN DEFAULT 0,
            download_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (upload_by) REFERENCES users (id),
            FOREIGN KEY (server_id) REFERENCES servers (id),
            FOREIGN KEY (feature_id) REFERENCES features (id)
        )
    ''')
    
    # 機能テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS features (
            id TEXT PRIMARY KEY,
            server_id TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            icon TEXT NOT NULL,
            position INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (server_id) REFERENCES servers (id)
        )
    ''')
    
    # コンテンツテーブル（JSON形式で様々なデータを保存）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feature_content (
            feature_id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (feature_id) REFERENCES features (id)
        )
    ''')
    
    # セッションテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect('data/circle_platform.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_current_user():
    if 'user_id' not in session:
        return None
    
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE id = ?', (session['user_id'],)
    ).fetchone()
    conn.close()
    
    if user:
        return {
            'id': user['id'],
            'username': user['username'],
            'nickname': user['nickname'] or user['username'],
            'admission_year': user['admission_year'],
            'avatar': user['avatar'],
            'ui_scale': user['ui_scale'],
            'theme': user['theme']
        }
    return None

def get_user_state(user_id):
    """ユーザーの全体的な状態を取得"""
    conn = get_db_connection()
    
    # ユーザーが参加しているサーバー一覧を取得
    servers = {}
    server_rows = conn.execute('''
        SELECT s.*, sm.role, sm.joined_at
        FROM servers s
        JOIN server_members sm ON s.id = sm.server_id
        WHERE sm.user_id = ?
        ORDER BY sm.joined_at
    ''', (user_id,)).fetchall()
    
    for server in server_rows:
        servers[server['id']] = {
            'id': server['id'],
            'name': server['name'],
            'description': server['description'],
            'icon': server['icon'],
            'banner': server['banner'],
            'owner_id': server['owner_id'],
            'is_public': server['is_public'],
            'invite_code': server['invite_code'],
            'userRole': server['role'],
            'joinedAt': server['joined_at']
        }
    
    # 各サーバーの機能を取得
    features = {}
    for server_id in servers.keys():
        feature_rows = conn.execute(
            'SELECT * FROM features WHERE server_id = ? ORDER BY position, created_at',
            (server_id,)
        ).fetchall()
        features[server_id] = []
        for feature in feature_rows:
            features[server_id].append({
                'id': feature['id'],
                'name': feature['name'],
                'type': feature['type'],
                'icon': feature['icon'],
                'server_id': feature['server_id']
            })
    
    # 各機能のコンテンツを取得
    content = {}
    content_rows = conn.execute('SELECT * FROM feature_content').fetchall()
    for row in content_rows:
        try:
            content[row['feature_id']] = json.loads(row['content'])
        except json.JSONDecodeError:
            content[row['feature_id']] = {}
    
    # ファイル情報を取得
    files = []
    if servers:
        placeholders = ','.join(['?' for _ in servers.keys()])
        file_rows = conn.execute(f'''
            SELECT f.*, u.username as uploader_name
            FROM files f
            LEFT JOIN users u ON f.upload_by = u.id
            WHERE f.server_id IN ({placeholders})
            ORDER BY f.created_at DESC
        ''', list(servers.keys())).fetchall()
    else:
        file_rows = []
    
    for file_row in file_rows:
        files.append({
            'id': file_row['id'],
            'filename': file_row['original_filename'],
            'serverId': file_row['server_id'],
            'featureId': file_row['feature_id'],
            'size': file_row['file_size'],
            'uploadedBy': file_row['uploader_name'],
            'uploadedAt': file_row['created_at'],
            'mimeType': file_row['mime_type'],
            'downloadCount': file_row['download_count']
        })
    
    conn.close()
    
    return {
        'servers': servers,
        'features': features,
        'content': content,
        'files': files,
        'currentUser': get_current_user(),
        'loggedIn': True
    }

def create_default_features(server_id):
    """新しいサーバーに標準機能を作成"""
    conn = get_db_connection()
    
    default_features = [
        {'name': 'チャット', 'type': 'chat', 'icon': 'message-circle'},
        {'name': 'フォーラム', 'type': 'forum', 'icon': 'message-square'},
        {'name': 'ホワイトボード', 'type': 'whiteboard', 'icon': 'edit-3'},
        {'name': 'ファイル共有', 'type': 'storage', 'icon': 'folder'},
        {'name': 'アンケート', 'type': 'survey', 'icon': 'clipboard-list'},
        {'name': 'プロジェクト', 'type': 'projects', 'icon': 'git-branch'},
        {'name': 'Wiki', 'type': 'wiki', 'icon': 'book'},
        {'name': 'カレンダー', 'type': 'calendar', 'icon': 'calendar'},
        {'name': '予算管理', 'type': 'budget', 'icon': 'dollar-sign'},
        {'name': '物品管理', 'type': 'inventory', 'icon': 'package'},
        {'name': 'メンバー', 'type': 'members', 'icon': 'users'},
        {'name': 'アルバム', 'type': 'album', 'icon': 'image'},
        {'name': '日記', 'type': 'diary', 'icon': 'edit'}
    ]
    
    for i, feature in enumerate(default_features):
        feature_id = f"{server_id}_{feature['type']}_{int(time.time() * 1000)}_{i}"
        conn.execute('''
            INSERT INTO features (id, server_id, name, type, icon, position)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (feature_id, server_id, feature['name'], feature['type'], feature['icon'], i))
        
        # 初期コンテンツを作成
        initial_content = create_initial_content(feature['type'])
        conn.execute('''
            INSERT INTO feature_content (feature_id, content)
            VALUES (?, ?)
        ''', (feature_id, json.dumps(initial_content)))
    
    conn.commit()
    conn.close()

def create_initial_content(feature_type):
    """機能タイプに基づいて初期コンテンツを作成"""
    if feature_type == 'chat':
        return {
            'subItems': {
                'general': {
                    'id': 'general',
                    'name': '一般',
                    'type': 'channel',
                    'messages': []
                }
            }
        }
    elif feature_type == 'forum':
        return {
            'subItems': {
                'announcements': {
                    'id': 'announcements',
                    'name': 'お知らせ',
                    'type': 'thread',
                    'posts': []
                }
            }
        }
    elif feature_type == 'whiteboard':
        return {
            'boards': {
                'main': {
                    'id': 'main',
                    'name': 'メインボード',
                    'elements': {}
                }
            }
        }
    elif feature_type == 'wiki':
        return {
            'pages': {
                'welcome': {
                    'id': 'welcome',
                    'title': 'ようこそ',
                    'content': 'このWikiページへようこそ！\n\n自由に編集してください。',
                    'author': 'システム',
                    'created_at': time.time(),
                    'updated_at': time.time(),
                    'tags': ['歓迎']
                }
            }
        }
    elif feature_type == 'calendar':
        return {'events': {}}
    elif feature_type == 'budget':
        return {
            'accounts': {},
            'transactions': {}
        }
    elif feature_type == 'inventory':
        return {
            'items': {},
            'categories': ['機材', '備品', '書籍', '電子機器'],
            'locations': ['メインオフィス', '倉庫', '研究室']
        }
    elif feature_type == 'members':
        return {
            'members': {},
            'roles': {
                'admin': {'name': '管理者', 'permissions': ['all']},
                'moderator': {'name': 'モデレーター', 'permissions': ['moderate']},
                'member': {'name': 'メンバー', 'permissions': ['basic']}
            }
        }
    elif feature_type == 'album':
        return {'albums': {}}
    elif feature_type == 'diary':
        return {'entries': {}}
    elif feature_type == 'survey':
        return {'surveys': {}, 'responses': {}}
    elif feature_type == 'projects':
        return {'projects': {}, 'tasks': {}}
    else:
        return {}

# APIエンドポイント
@app.route('/')
def index():
    return send_file('index.html')


@app.route('/favicon.ico')
def favicon():
    # Return 204 No Content for favicon requests to avoid noisy 404s in the browser console
    return ('', 204)

@app.route('/files/<path:filename>')
def serve_file(filename):
    """ファイルを安全に配信"""
    try:
        return send_from_directory('files', filename)
    except Exception as e:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api.cgi', methods=['POST'])
def api_handler():
    action = request.form.get('action')
    
    try:
        if action == 'login':
            return handle_login()
        elif action == 'register':
            return handle_register()
        elif action == 'logout':
            return handle_logout()
        elif action == 'checkSession':
            return handle_check_session()
        elif action == 'addServer':
            return handle_add_server()
        elif action == 'addSubItem':
            return handle_add_subitem()
        elif action == 'addWhiteboard':
            return handle_add_whiteboard()
        elif action == 'saveWhiteboard':
            return handle_save_whiteboard()
        elif action == 'postMessage':
            return handle_post_message()
        elif action == 'createSurvey':
            return handle_create_survey()
        elif action == 'submitSurveyResponse':
            return handle_submit_survey_response()
        elif action == 'createProject':
            return handle_create_project()
        elif action == 'createTask':
            return handle_create_task()
        elif action == 'updateTaskStatus':
            return handle_update_task_status()
        elif action == 'updateProfile':
            return handle_update_profile()
        elif action == 'uploadFile':
            return handle_upload_file()
        elif action == 'createInvite':
            return handle_create_invite()
        elif action == 'acceptInvite':
            return handle_accept_invite()
        elif action == 'updateMemberRole':
            return handle_update_member_role()
        elif action == 'requestPasswordRecovery':
            return handle_request_password_recovery()
        elif action == 'approvePasswordRecovery':
            return handle_approve_password_recovery()
        elif action == 'resetPassword':
            return handle_reset_password()
        elif action == 'getServerMembers':
            return handle_get_server_members()
        elif action == 'saveWhiteboardImage':
            return handle_save_whiteboard_image()
        elif action == 'updateFeatureContent':
            return handle_update_feature_content()
        elif action == 'getFeatureContent':
            return handle_get_feature_content()
        else:
            return jsonify({'success': False, 'error': f'Unknown action: {action}'})
    
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'success': False, 'error': str(e)})

def handle_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username:
        return jsonify({'success': False, 'error': 'ユーザー名を入力してください'})
    
    if not password:
        return jsonify({'success': False, 'error': 'パスワードを入力してください'})
    
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ?', (username,)
    ).fetchone()
    
    if not user:
        conn.close()
        return jsonify({'success': False, 'error': 'ユーザー名が見つかりません'})
    
    # パスワード確認
    provided_hash = hash_password(password)
    if user['password_hash'] != provided_hash:
        conn.close()
        return jsonify({'success': False, 'error': 'パスワードが間違っています'})
    
    # ログイン成功 - 最終ログイン時刻を更新
    conn.execute(
        'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
        (user['id'],)
    )
    conn.commit()
    conn.close()
    
    session['user_id'] = user['id']
    session['username'] = user['username']
    
    state = get_user_state(user['id'])
    return jsonify({'success': True, 'data': {'loggedIn': True, 'state': state}})

def handle_register():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'})
    
    if len(username) < 3:
        return jsonify({'success': False, 'error': 'Username must be at least 3 characters'})
    
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'})
    
    conn = get_db_connection()
    
    # Check if user exists
    existing_user = conn.execute(
        'SELECT id FROM users WHERE username = ?', (username,)
    ).fetchone()
    
    if existing_user:
        conn.close()
        return jsonify({'success': False, 'error': 'Username already exists'})
    
    # Create new user
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
        ''', (username, hash_password(password)))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'data': {'message': 'User registered successfully'}})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

def handle_logout():
    session.clear()
    return jsonify({'success': True, 'data': {'message': 'Logged out successfully'}})

def handle_check_session():
    user = get_current_user()
    if user:
        state = get_user_state(user['id'])
        return jsonify({'success': True, 'data': {'loggedIn': True, 'state': state}})
    else:
        return jsonify({'success': True, 'data': {'loggedIn': False}})

def handle_add_server():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    name = request.form.get('name')
    icon = request.form.get('icon', '🎯')
    
    if not name:
        return jsonify({'success': False, 'error': 'Server name is required'})
    
    server_id = f"server_{int(time.time() * 1000)}"
    invite_code = secrets.token_urlsafe(8)
    
    conn = get_db_connection()
    
    # サーバーを作成
    conn.execute('''
        INSERT INTO servers (id, name, icon, owner_id, invite_code)
        VALUES (?, ?, ?, ?, ?)
    ''', (server_id, name, icon, user['id'], invite_code))
    
    # オーナーをメンバーとして追加
    conn.execute('''
        INSERT INTO server_members (server_id, user_id, role)
        VALUES (?, ?, 'owner')
    ''', (server_id, user['id']))
    
    conn.commit()
    conn.close()
    
    # デフォルト機能を作成
    create_default_features(server_id)
    
    # 最新の状態を返す
    state = get_user_state(user['id'])
    return jsonify({'success': True, 'data': state})

def handle_add_subitem():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    feature_id = request.form.get('featureId')
    name = request.form.get('name')
    item_type = request.form.get('type', 'channel')
    
    if not feature_id or not name:
        return jsonify({'success': False, 'error': 'Feature ID and name are required'})
    
    conn = get_db_connection()
    content_row = conn.execute(
        'SELECT content FROM feature_content WHERE feature_id = ?', (feature_id,)
    ).fetchone()
    
    if not content_row:
        conn.close()
        return jsonify({'success': False, 'error': 'Feature not found'})
    
    content = json.loads(content_row['content'])
    if 'subItems' not in content:
        content['subItems'] = {}
    
    subitem_id = f"{item_type}_{int(time.time() * 1000)}"
    content['subItems'][subitem_id] = {
        'id': subitem_id,
        'name': name,
        'type': item_type,
        'messages': [] if item_type == 'channel' else [],
        'posts': [] if item_type == 'thread' else []
    }
    
    conn.execute('''
        UPDATE feature_content 
        SET content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE feature_id = ?
    ''', (json.dumps(content), feature_id))
    conn.commit()
    conn.close()
    
    state = get_user_state(user['id'])
    return jsonify({'success': True, 'data': state})

def handle_add_whiteboard():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    feature_id = request.form.get('featureId')
    name = request.form.get('name')
    
    if not feature_id or not name:
        return jsonify({'success': False, 'error': 'Feature ID and name are required'})
    
    conn = get_db_connection()
    content_row = conn.execute(
        'SELECT content FROM feature_content WHERE feature_id = ?', (feature_id,)
    ).fetchone()
    
    if not content_row:
        conn.close()
        return jsonify({'success': False, 'error': 'Feature not found'})
    
    content = json.loads(content_row['content'])
    if 'boards' not in content:
        content['boards'] = {}
    
    board_id = f"board_{int(time.time() * 1000)}"
    content['boards'][board_id] = {
        'id': board_id,
        'name': name,
        'elements': {},
        'created_by': user['username'],
        'created_at': time.time()
    }
    
    conn.execute('''
        UPDATE feature_content 
        SET content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE feature_id = ?
    ''', (json.dumps(content), feature_id))
    conn.commit()
    conn.close()
    
    state = get_user_state(user['id'])
    return jsonify({'success': True, 'data': state})

def handle_save_whiteboard():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    feature_id = request.form.get('featureId')
    board_id = request.form.get('boardId')
    elements = request.form.get('elements')
    
    if not feature_id or not board_id or not elements:
        return jsonify({'success': False, 'error': 'Feature ID, board ID, and elements are required'})
    
    conn = get_db_connection()
    content_row = conn.execute(
        'SELECT content FROM feature_content WHERE feature_id = ?', (feature_id,)
    ).fetchone()
    
    if not content_row:
        conn.close()
        return jsonify({'success': False, 'error': 'Feature not found'})
    
    content = json.loads(content_row['content'])
    if 'boards' not in content or board_id not in content['boards']:
        conn.close()
        return jsonify({'success': False, 'error': 'Board not found'})
    
    try:
        content['boards'][board_id]['elements'] = json.loads(elements)
        content['boards'][board_id]['updated_at'] = time.time()
    except json.JSONDecodeError:
        conn.close()
        return jsonify({'success': False, 'error': 'Invalid elements data'})
    
    conn.execute('''
        UPDATE feature_content 
        SET content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE feature_id = ?
    ''', (json.dumps(content), feature_id))
    conn.commit()
    conn.close()
    
    state = get_user_state(user['id'])
    return jsonify({'success': True, 'data': state})

def handle_post_message():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    feature_id = request.form.get('featureId')
    sub_item_id = request.form.get('subItemId')
    content_text = request.form.get('content')
    
    if not feature_id or not sub_item_id or not content_text:
        return jsonify({'success': False, 'error': 'Feature ID, sub item ID, and content are required'})
    
    conn = get_db_connection()
    content_row = conn.execute(
        'SELECT content FROM feature_content WHERE feature_id = ?', (feature_id,)
    ).fetchone()
    
    if not content_row:
        conn.close()
        return jsonify({'success': False, 'error': 'Feature not found'})
    
    content = json.loads(content_row['content'])
    if 'subItems' not in content or sub_item_id not in content['subItems']:
        conn.close()
        return jsonify({'success': False, 'error': 'Sub item not found'})
    
    message = {
        'id': str(uuid.uuid4()),
        'authorId': user['username'],
        'authorName': user['nickname'],
        'content': content_text,
        'timestamp': int(time.time())
    }
    
    subitem = content['subItems'][sub_item_id]
    if subitem['type'] == 'channel':
        if 'messages' not in subitem:
            subitem['messages'] = []
        subitem['messages'].append(message)
    elif subitem['type'] == 'thread':
        if 'posts' not in subitem:
            subitem['posts'] = []
        subitem['posts'].append(message)
    
    conn.execute('''
        UPDATE feature_content 
        SET content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE feature_id = ?
    ''', (json.dumps(content), feature_id))
    conn.commit()
    conn.close()
    
    state = get_user_state(user['id'])
    return jsonify({'success': True, 'data': state})

def handle_create_survey():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    feature_id = request.form.get('featureId')
    title = request.form.get('title')
    questions_json = request.form.get('questions')
    
    if not feature_id or not title or not questions_json:
        return jsonify({'success': False, 'error': 'Feature ID, title, and questions are required'})
    
    try:
        questions = json.loads(questions_json)
    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': 'Invalid questions format'})
    
    conn = get_db_connection()
    content_row = conn.execute(
        'SELECT content FROM feature_content WHERE feature_id = ?', (feature_id,)
    ).fetchone()
    
    if not content_row:
        conn.close()
        return jsonify({'success': False, 'error': 'Feature not found'})
    
    content = json.loads(content_row['content'])
    if 'surveys' not in content:
        content['surveys'] = {}
    if 'responses' not in content:
        content['responses'] = {}
    
    survey_id = f"survey_{int(time.time() * 1000)}"
    content['surveys'][survey_id] = {
        'id': survey_id,
        'title': title,
        'questions': questions,
        'created_by': user['username'],
        'created_at': time.time(),
        'status': 'active'
    }
    content['responses'][survey_id] = {}
    
    conn.execute('''
        UPDATE feature_content 
        SET content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE feature_id = ?
    ''', (json.dumps(content), feature_id))
    conn.commit()
    conn.close()
    
    state = get_user_state(user['id'])
    return jsonify({'success': True, 'data': state})

def handle_submit_survey_response():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    feature_id = request.form.get('featureId')
    survey_id = request.form.get('surveyId')
    responses_json = request.form.get('responses')
    
    if not feature_id or not survey_id or not responses_json:
        return jsonify({'success': False, 'error': 'Feature ID, survey ID, and responses are required'})
    
    try:
        responses = json.loads(responses_json)
    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': 'Invalid responses format'})
    
    conn = get_db_connection()
    content_row = conn.execute(
        'SELECT content FROM feature_content WHERE feature_id = ?', (feature_id,)
    ).fetchone()
    
    if not content_row:
        conn.close()
        return jsonify({'success': False, 'error': 'Feature not found'})
    
    content = json.loads(content_row['content'])
    if 'responses' not in content:
        content['responses'] = {}
    if survey_id not in content['responses']:
        content['responses'][survey_id] = {}
    
    content['responses'][survey_id][user['username']] = {
        'responses': responses,
        'user': user['username'],
        'submitted_at': time.time()
    }
    
    conn.execute('''
        UPDATE feature_content 
        SET content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE feature_id = ?
    ''', (json.dumps(content), feature_id))
    conn.commit()
    conn.close()
    
    state = get_user_state(user['id'])
    return jsonify({'success': True, 'data': state})

def handle_create_project():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    feature_id = request.form.get('featureId')
    name = request.form.get('name')
    description = request.form.get('description', '')
    
    if not feature_id or not name:
        return jsonify({'success': False, 'error': 'Feature ID and name are required'})
    
    conn = get_db_connection()
    content_row = conn.execute(
        'SELECT content FROM feature_content WHERE feature_id = ?', (feature_id,)
    ).fetchone()
    
    if not content_row:
        conn.close()
        return jsonify({'success': False, 'error': 'Feature not found'})
    
    content = json.loads(content_row['content'])
    if 'projects' not in content:
        content['projects'] = {}
    
    project_id = f"project_{int(time.time() * 1000)}"
    content['projects'][project_id] = {
        'id': project_id,
        'name': name,
        'description': description,
        'status': 'active',
        'created_by': user['username'],
        'created_at': time.time()
    }
    
    conn.execute('''
        UPDATE feature_content 
        SET content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE feature_id = ?
    ''', (json.dumps(content), feature_id))
    conn.commit()
    conn.close()
    
    state = get_user_state(user['id'])
    return jsonify({'success': True, 'data': state})

def handle_create_task():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    feature_id = request.form.get('featureId')
    project_id = request.form.get('projectId')
    title = request.form.get('title')
    description = request.form.get('description', '')
    priority = request.form.get('priority', 'medium')
    
    if not feature_id or not project_id or not title:
        return jsonify({'success': False, 'error': 'Feature ID, project ID, and title are required'})
    
    conn = get_db_connection()
    content_row = conn.execute(
        'SELECT content FROM feature_content WHERE feature_id = ?', (feature_id,)
    ).fetchone()
    
    if not content_row:
        conn.close()
        return jsonify({'success': False, 'error': 'Feature not found'})
    
    content = json.loads(content_row['content'])
    if 'tasks' not in content:
        content['tasks'] = {}
    
    task_id = f"task_{int(time.time() * 1000)}"
    content['tasks'][task_id] = {
        'id': task_id,
        'project_id': project_id,
        'title': title,
        'description': description,
        'priority': priority,
        'status': 'todo',
        'created_by': user['username'],
        'created_at': time.time()
    }
    
    conn.execute('''
        UPDATE feature_content 
        SET content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE feature_id = ?
    ''', (json.dumps(content), feature_id))
    conn.commit()
    conn.close()
    
    state = get_user_state(user['id'])
    return jsonify({'success': True, 'data': state})

def handle_update_task_status():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    feature_id = request.form.get('featureId')
    task_id = request.form.get('taskId')
    status = request.form.get('status')
    
    if not feature_id or not task_id or not status:
        return jsonify({'success': False, 'error': 'Feature ID, task ID, and status are required'})
    
    conn = get_db_connection()
    content_row = conn.execute(
        'SELECT content FROM feature_content WHERE feature_id = ?', (feature_id,)
    ).fetchone()
    
    if not content_row:
        conn.close()
        return jsonify({'success': False, 'error': 'Feature not found'})
    
    content = json.loads(content_row['content'])
    if 'tasks' not in content or task_id not in content['tasks']:
        conn.close()
        return jsonify({'success': False, 'error': 'Task not found'})
    
    content['tasks'][task_id]['status'] = status
    content['tasks'][task_id]['updated_at'] = time.time()
    
    conn.execute('''
        UPDATE feature_content 
        SET content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE feature_id = ?
    ''', (json.dumps(content), feature_id))
    conn.commit()
    conn.close()
    
    state = get_user_state(user['id'])
    return jsonify({'success': True, 'data': state})

def handle_update_profile():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    conn = get_db_connection()
    
    # 更新可能なフィールド
    fields = {}
    if request.form.get('nickname'):
        fields['nickname'] = request.form.get('nickname')
    if request.form.get('email'):
        fields['email'] = request.form.get('email')
    if request.form.get('admission_year'):
        try:
            fields['admission_year'] = int(request.form.get('admission_year'))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': '入学年は数字で入力してください'})
    if request.form.get('graduation_year'):
        try:
            fields['graduation_year'] = int(request.form.get('graduation_year'))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': '卒業年は数字で入力してください'})
    if request.form.get('major'):
        fields['major'] = request.form.get('major')
    if request.form.get('student_id'):
        fields['student_id'] = request.form.get('student_id')
    if request.form.get('bio'):
        fields['bio'] = request.form.get('bio')
    if request.form.get('theme'):
        fields['theme'] = request.form.get('theme')
    if request.form.get('ui_scale'):
        fields['ui_scale'] = request.form.get('ui_scale')
    if request.form.get('language'):
        fields['language'] = request.form.get('language')
    if request.form.get('timezone'):
        fields['timezone'] = request.form.get('timezone')
    
    if not fields:
        conn.close()
        return jsonify({'success': False, 'error': '更新するフィールドがありません'})
    
    # SQLの更新クエリを構築
    set_clause = ', '.join([f"{k} = ?" for k in fields.keys()])
    values = list(fields.values()) + [user['id']]
    
    conn.execute(f'''
        UPDATE users 
        SET {set_clause}, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', values)
    conn.commit()
    conn.close()
    
    state = get_user_state(user['id'])
    return jsonify({'success': True, 'data': state})

def handle_upload_file():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'ファイルが選択されていません'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'ファイルが選択されていません'})
    
    server_id = request.form.get('serverId')
    feature_id = request.form.get('featureId')
    
    # ファイルサイズ制限（10MB）
    if len(file.read()) > 10 * 1024 * 1024:
        return jsonify({'success': False, 'error': 'ファイルサイズは10MB以下にしてください'})
    file.seek(0)  # ファイルポインタを先頭に戻す
    
    # 安全なファイル名を生成
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    safe_filename = f"{file_id}{file_extension}"
    
    # ファイルを保存
    file_path = os.path.join('files', 'uploads', safe_filename)
    file.save(file_path)
    
    # データベースに記録
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO files (id, filename, original_filename, file_path, file_size, 
                          mime_type, upload_by, server_id, feature_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (file_id, safe_filename, file.filename, file_path, 
          os.path.getsize(file_path), file.content_type or 'application/octet-stream',
          user['id'], server_id, feature_id))
    conn.commit()
    conn.close()
    # 返却データに保存後の安全なファイル名とURLを含める
    stored_filename = safe_filename
    file_url = f"/files/uploads/{stored_filename}"
    return jsonify({'success': True, 'data': {
        'fileId': file_id,
        'originalFilename': file.filename,
        'storedFilename': stored_filename,
        'fileSize': os.path.getsize(file_path),
        'url': file_url
    }})

def handle_create_invite():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    server_id = request.form.get('serverId')
    if not server_id:
        return jsonify({'success': False, 'error': 'サーバーIDが必要です'})
    
    conn = get_db_connection()
    
    # サーバーの管理者権限を確認
    membership = conn.execute('''
        SELECT role FROM server_members 
        WHERE server_id = ? AND user_id = ?
    ''', (server_id, user['id'])).fetchone()
    
    if not membership or membership['role'] not in ['owner', 'admin']:
        conn.close()
        return jsonify({'success': False, 'error': '招待する権限がありません'})
    
    # 招待コードを生成
    invite_code = secrets.token_urlsafe(8)
    invite_id = str(uuid.uuid4())
    
    # 有効期限（24時間後）
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    conn.execute('''
        INSERT INTO server_invites (id, server_id, inviter_id, invite_code, expires_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (invite_id, server_id, user['id'], invite_code, expires_at))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'data': {
        'inviteId': invite_id,
        'inviteCode': invite_code,
        'expiresAt': expires_at.isoformat()
    }})

def handle_accept_invite():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    invite_code = request.form.get('inviteCode')
    if not invite_code:
        return jsonify({'success': False, 'error': '招待コードが必要です'})
    
    conn = get_db_connection()
    
    # 招待コードを確認
    invite = conn.execute('''
        SELECT * FROM server_invites 
        WHERE invite_code = ? AND used_at IS NULL AND expires_at > CURRENT_TIMESTAMP
    ''', (invite_code,)).fetchone()
    
    if not invite:
        conn.close()
        return jsonify({'success': False, 'error': '無効または期限切れの招待コードです'})
    
    # 既にメンバーかどうか確認
    existing_member = conn.execute('''
        SELECT id FROM server_members 
        WHERE server_id = ? AND user_id = ?
    ''', (invite['server_id'], user['id'])).fetchone()
    
    if existing_member:
        conn.close()
        return jsonify({'success': False, 'error': '既にこのサーバーのメンバーです'})
    
    # メンバーとして追加
    conn.execute('''
        INSERT INTO server_members (server_id, user_id, role, invited_by)
        VALUES (?, ?, 'member', ?)
    ''', (invite['server_id'], user['id'], invite['inviter_id']))
    
    # 招待を使用済みにマーク
    conn.execute('''
        UPDATE server_invites 
        SET used_at = CURRENT_TIMESTAMP, used_by = ?, current_uses = current_uses + 1
        WHERE id = ?
    ''', (user['id'], invite['id']))
    
    conn.commit()
    conn.close()
    
    state = get_user_state(user['id'])
    return jsonify({'success': True, 'data': state})

def handle_update_member_role():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    server_id = request.form.get('serverId')
    target_user_id = request.form.get('userId')
    new_role = request.form.get('role')
    
    if not all([server_id, target_user_id, new_role]):
        return jsonify({'success': False, 'error': '必要なパラメータが不足しています'})
    
    if new_role not in ['member', 'moderator', 'admin']:
        return jsonify({'success': False, 'error': '無効なロールです'})
    
    conn = get_db_connection()
    
    # 管理者権限を確認
    admin_role = conn.execute('''
        SELECT role FROM server_members 
        WHERE server_id = ? AND user_id = ?
    ''', (server_id, user['id'])).fetchone()
    
    if not admin_role or admin_role['role'] not in ['owner', 'admin']:
        conn.close()
        return jsonify({'success': False, 'error': 'ロールを変更する権限がありません'})
    
    # ロールを更新
    conn.execute('''
        UPDATE server_members 
        SET role = ? 
        WHERE server_id = ? AND user_id = ?
    ''', (new_role, server_id, target_user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'data': {'message': 'ロールを更新しました'}})

def handle_request_password_recovery():
    username = request.form.get('username')
    partner_username = request.form.get('partnerUsername')
    
    if not username or not partner_username:
        return jsonify({'success': False, 'error': 'ユーザー名とパートナーのユーザー名が必要です'})
    
    conn = get_db_connection()
    
    # ユーザーを確認
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    partner = conn.execute('SELECT * FROM users WHERE username = ?', (partner_username,)).fetchone()
    
    if not user or not partner:
        conn.close()
        return jsonify({'success': False, 'error': 'ユーザーが見つかりません'})
    
    # 既存のリクエストを確認
    existing = conn.execute('''
        SELECT * FROM password_recovery 
        WHERE user_id = ? AND recovery_partner_id = ? AND status = 'pending'
    ''', (user['id'], partner['id'])).fetchone()
    
    if existing:
        conn.close()
        return jsonify({'success': False, 'error': '既にパスワード復旧リクエストが存在します'})
    
    # 復旧トークンを生成
    recovery_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    conn.execute('''
        INSERT INTO password_recovery (user_id, recovery_partner_id, initiated_by, recovery_token, expires_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user['id'], partner['id'], user['id'], recovery_token, expires_at))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'data': {
        'message': 'パスワード復旧リクエストを送信しました',
        'recoveryToken': recovery_token
    }})

def handle_approve_password_recovery():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    recovery_token = request.form.get('recoveryToken')
    if not recovery_token:
        return jsonify({'success': False, 'error': '復旧トークンが必要です'})
    
    conn = get_db_connection()
    
    # 復旧リクエストを確認
    recovery = conn.execute('''
        SELECT * FROM password_recovery 
        WHERE recovery_token = ? AND recovery_partner_id = ? AND status = 'pending'
    ''', (recovery_token, user['id'])).fetchone()
    
    if not recovery:
        conn.close()
        return jsonify({'success': False, 'error': '無効な復旧トークンです'})
    
    # 承認
    conn.execute('''
        UPDATE password_recovery 
        SET status = 'approved', approved_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (recovery['id'],))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'data': {'message': 'パスワード復旧を承認しました'}})

def handle_reset_password():
    recovery_token = request.form.get('recoveryToken')
    new_password = request.form.get('newPassword')
    
    if not recovery_token or not new_password:
        return jsonify({'success': False, 'error': '復旧トークンと新パスワードが必要です'})
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'パスワードは6文字以上にしてください'})
    
    conn = get_db_connection()
    
    # 承認済みの復旧リクエストを確認
    recovery = conn.execute('''
        SELECT * FROM password_recovery 
        WHERE recovery_token = ? AND status = 'approved' AND expires_at > CURRENT_TIMESTAMP
    ''', (recovery_token,)).fetchone()
    
    if not recovery:
        conn.close()
        return jsonify({'success': False, 'error': '無効または期限切れの復旧トークンです'})
    
    # パスワードを更新
    new_hash = hash_password(new_password)
    conn.execute('''
        UPDATE users 
        SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (new_hash, recovery['user_id']))
    
    # 復旧リクエストを完了にマーク
    conn.execute('''
        UPDATE password_recovery 
        SET status = 'completed', completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (recovery['id'],))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'data': {'message': 'パスワードをリセットしました'}})

def handle_get_server_members():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    server_id = request.form.get('serverId')
    if not server_id:
        return jsonify({'success': False, 'error': 'サーバーIDが必要です'})
    
    conn = get_db_connection()
    
    # メンバーシップを確認
    membership = conn.execute('''
        SELECT role FROM server_members 
        WHERE server_id = ? AND user_id = ?
    ''', (server_id, user['id'])).fetchone()
    
    if not membership:
        conn.close()
        return jsonify({'success': False, 'error': 'サーバーのメンバーではありません'})
    
    # メンバー一覧を取得
    members = conn.execute('''
        SELECT u.id, u.username, u.nickname, u.avatar, sm.role, sm.joined_at
        FROM server_members sm
        JOIN users u ON sm.user_id = u.id
        WHERE sm.server_id = ?
        ORDER BY sm.joined_at
    ''', (server_id,)).fetchall()
    
    conn.close()
    
    member_list = []
    for member in members:
        member_list.append({
            'id': member['id'],
            'username': member['username'],
            'nickname': member['nickname'] or member['username'],
            'avatar': member['avatar'],
            'role': member['role'],
            'joinedAt': member['joined_at']
        })
    
    return jsonify({'success': True, 'data': {'members': member_list}})

def handle_save_whiteboard_image():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    feature_id = request.form.get('featureId')
    board_id = request.form.get('boardId')
    image_data = request.form.get('imageData')
    
    if not all([feature_id, board_id, image_data]):
        return jsonify({'success': False, 'error': '必要なパラメータが不足しています'})
    
    try:
        # Base64データをデコード
        import base64
        header, encoded = image_data.split(',', 1)
        image_bytes = base64.b64decode(encoded)
        
        # ファイルを保存
        image_id = str(uuid.uuid4())
        file_path = os.path.join('files', 'whiteboards', f"{image_id}.png")
        
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        
        # データベースに記録
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO files (id, filename, original_filename, file_path, file_size, 
                              mime_type, upload_by, feature_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (image_id, f"{image_id}.png", f"whiteboard_{board_id}.png", 
              file_path, len(image_bytes), 'image/png', user['id'], feature_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'data': {
            'imageId': image_id,
            'imagePath': file_path
        }})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'画像保存エラー: {str(e)}'})

def handle_update_feature_content():
    """機能のコンテンツを更新する汎用的なハンドラー"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    feature_id = request.form.get('featureId')
    content_data = request.form.get('content')
    
    if not feature_id or not content_data:
        return jsonify({'success': False, 'error': 'Feature ID and content are required'})
    
    try:
        # JSONデータの検証
        content = json.loads(content_data)
        
        conn = get_db_connection()
        
        # 既存のコンテンツを取得
        existing_row = conn.execute(
            'SELECT content FROM feature_content WHERE feature_id = ?', (feature_id,)
        ).fetchone()
        
        if existing_row:
            # 既存コンテンツを更新
            conn.execute('''
                UPDATE feature_content 
                SET content = ?, updated_at = CURRENT_TIMESTAMP
                WHERE feature_id = ?
            ''', (json.dumps(content), feature_id))
        else:
            # 新規コンテンツを作成
            conn.execute('''
                INSERT INTO feature_content (feature_id, content, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (feature_id, json.dumps(content)))
        
        conn.commit()
        conn.close()
        
        # 更新された状態を返す
        state = get_user_state(user['id'])
        return jsonify({'success': True, 'data': state})
        
    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'})

def handle_get_feature_content():
    """機能のコンテンツを取得する"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    feature_id = request.form.get('featureId')
    
    if not feature_id:
        return jsonify({'success': False, 'error': 'Feature ID is required'})
    
    conn = get_db_connection()
    content_row = conn.execute(
        'SELECT content FROM feature_content WHERE feature_id = ?', (feature_id,)
    ).fetchone()
    conn.close()
    
    if content_row:
        try:
            content = json.loads(content_row['content'])
            return jsonify({'success': True, 'data': content})
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': 'Invalid content data'})
    else:
        return jsonify({'success': True, 'data': {}})

if __name__ == '__main__':
    init_database()
    print("Database initialized")
    print("Starting Circle Management Platform on port 8060...")
    app.run(host='0.0.0.0', port=8060, debug=True)
