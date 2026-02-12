import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'database.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    role TEXT
)
""")

# BARBER SHOPS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS barber_shops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barber_id INTEGER,
    shop_name TEXT,
    address TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER,
    name TEXT,
    price INTEGER,
    duration INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id INTEGER,
    date TEXT,
    start_time TEXT,
    end_time TEXT,
    is_available INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    slot_id INTEGER,
    status TEXT
)
""")

conn.commit()
conn.close()

print("All tables created successfully ✅")
