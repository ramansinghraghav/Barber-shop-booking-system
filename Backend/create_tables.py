from db import get_db_connection

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            phone TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    # BARBER SHOPS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS barber_shops (
            id SERIAL PRIMARY KEY,
            barber_id INTEGER,
            shop_name TEXT,
            address TEXT,
            open_time TEXT,
            close_time TEXT
        )
    """)

    # SERVICES
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id SERIAL PRIMARY KEY,
            shop_id INTEGER,
            name TEXT,
            price INTEGER,
            duration INTEGER
        )
    """)

    # SLOTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            id SERIAL PRIMARY KEY,
            service_id INTEGER,
            date DATE,
            start_time TEXT,
            end_time TEXT,
            is_available BOOLEAN DEFAULT TRUE
        )
    """)

    # BOOKINGS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            slot_id INTEGER,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()

    print("All tables created successfully ✅")
