import sqlite3
from datetime import datetime
import os

DB_PATH = "bot_database.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            join_date TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_type TEXT,
            target_link TEXT,
            quantity INTEGER,
            status TEXT,
            created_at TEXT,
            completed_at TEXT,
            result_count INTEGER DEFAULT 0
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            order_id INTEGER PRIMARY KEY,
            current INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            last_update TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS source_groups_db (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT UNIQUE,
            chat_title TEXT,
            added_by INTEGER,
            added_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name):
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id, username, first_name, join_date) VALUES (?, ?, ?, ?)',
              (user_id, username, first_name, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def add_order(user_id, order_type, target_link, quantity):
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO orders (user_id, order_type, target_link, quantity, status, created_at) VALUES (?, ?, ?, ?, ?, ?)',
              (user_id, order_type, target_link, quantity, 'pending', datetime.now().isoformat()))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO progress (order_id, current, total, last_update) VALUES (?, ?, ?, ?)',
              (order_id, 0, quantity, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return order_id

def update_progress(order_id, current):
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE progress SET current = ?, last_update = ? WHERE order_id = ?',
              (current, datetime.now().isoformat(), order_id))
    conn.commit()
    conn.close()

def update_order_status(order_id, status, result_count=0):
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE orders SET status = ?, completed_at = ?, result_count = ? WHERE id = ?',
              (status, datetime.now().isoformat(), result_count, order_id))
    conn.commit()
    conn.close()

def get_user_today_orders(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders WHERE user_id = ? AND date(created_at) = date('now')", (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def get_source_groups():
    groups = []
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT chat_id FROM source_groups_db')
        groups = [row[0] for row in c.fetchall()]
        conn.close()
    except Exception as e:
        print(f"خطا در دریافت گروه‌های منبع: {e}")
    return groups

def add_source_group(chat_id, chat_title, user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO source_groups_db (chat_id, chat_title, added_by, added_at)
        VALUES (?, ?, ?, ?)
    ''', (chat_id, chat_title, user_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True

def remove_source_group(chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM source_groups_db WHERE chat_id = ?', (chat_id,))
    conn.commit()
    conn.close()
    return True

def get_all_source_groups():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, chat_id, chat_title, added_at FROM source_groups_db')
    groups = c.fetchall()
    conn.close()
    return groups
