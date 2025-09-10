import sqlite3, hashlib, os
p=os.path.join('data','circle_platform.db')
if not os.path.exists(p):
    print('DB missing:', p)
else:
    newpw='Password123!'
    hashv=hashlib.sha256(newpw.encode()).hexdigest()
    conn=sqlite3.connect(p)
    cur=conn.cursor()
    cur.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hashv,'lorinta'))
    conn.commit()
    cur.execute("SELECT id, username FROM users WHERE username='lorinta'")
    print('Updated:', cur.fetchall())
    conn.close()
