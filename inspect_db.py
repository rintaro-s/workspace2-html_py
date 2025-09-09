import sqlite3, os, json
path = os.path.join('data', 'circle_platform.db')
print('DB PATH:', path)
print('EXISTS:', os.path.exists(path))
if not os.path.exists(path):
    raise SystemExit('Database file not found')
conn = sqlite3.connect(path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('TABLES:', tables)
if 'users' in tables:
    cur.execute('SELECT id, username, nickname, created_at FROM users')
    rows = cur.fetchall()
    print('USERS_COUNT:', len(rows))
    for r in rows:
        print(r)
else:
    print('No users table')
conn.close()
