from werkzeug.security import generate_password_hash,check_password_hash
from flask import Flask, request
from flask_cors import CORS
from datetime import datetime, timedelta
import sqlite3
import time
import os
import jwt
from functools import wraps
from dotenv import load_dotenv
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
# ✅ ADD THIS CHECK HERE
if not JWT_SECRET or not FLASK_SECRET_KEY:
    raise Exception("Missing secrets in .env file")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_db_connection():
    conn = sqlite3.connect(
        os.path.join(BASE_DIR, 'database.db'),
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


app = Flask (__name__)
app.secret_key = FLASK_SECRET_KEY

CORS(app)

def token_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization")

            if not auth:
                return {"success": False, "message": "Token missing"}, 401

            try:
                token = auth.split(" ")[1]
                data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return {"success": False, "message": "Token expired"}, 401
            except jwt.InvalidTokenError:
                return {"success": False, "message": "Invalid token"}, 401
            request.user = data

            if role and data["role"] != role:
                return {"success": False, "message": "Access denied"}, 403

            return f(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/')
def home():
    return "Server running successfully"

@app.route("/api/services", methods=["GET"])
@token_required(role="customer")
def get_services():
    conn = get_db_connection()
    services = conn.execute("""
        SELECT services.id, services.name, services.price, services.duration
        FROM services
    """).fetchall()
    conn.close()

    return {
        "services": [dict(s) for s in services]
    }
def generate_token(user):
    payload = {
        "user_id": user["id"],
        "role": user["role"],
        "exp": int(time.time()) + 3600
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()

        if not data:
            return {"success": False, "message": "JSON body required"}, 400

        phone = data.get("phone")
        password = data.get("password")

        if not phone or not password:
            return {"success": False, "message": "Phone and password required"}, 400

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE phone = ?",
            (phone,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            token = generate_token(user)
            return {"success": True, "token": token}

        return {"success": False, "message": "Invalid credentials"}, 401

    except Exception as e:
        return {"success": False, "error": str(e)}, 500

    finally:
        if 'conn' in locals():
            conn.close()


@app.route('/api/signup', methods=['POST'])
def api_signup():
    try:
        data = request.get_json()

        if not data:
            return {"success": False, "message": "JSON body required"}, 400

        name = data.get('name')
        phone = data.get('phone')
        raw_password = data.get('password')
        role = data.get('role')

        if not name or not phone or not raw_password or not role:
            return {"success": False, "message": "name, phone, password, role required"}, 400

        password = generate_password_hash(raw_password)

        conn = get_db_connection()

        # duplicate check
        existing = conn.execute(
            "SELECT id FROM users WHERE phone=?",
            (phone,)
        ).fetchone()

        if existing:
            return {"success": False, "message": "Phone already registered"}, 409

        # insert user
        conn.execute(
            "INSERT INTO users (name, phone, password, role) VALUES (?, ?, ?, ?)",
            (name, phone, password, role)
        )

        conn.commit()
        return {"success": True, "message": "User created successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}, 500

    finally:
        if 'conn' in locals():
            conn.close()


@app.route('/api/shop', methods=['POST'])
@token_required(role="barber")
def api_add_shop():
    data = request.get_json()

    if not data:
        return {"success": False, "message": "JSON body required"}, 400

    barber_id = request.user["user_id"]
    shop_name = data.get('shop_name')
    address = data.get('address')
    open_time = data.get('open_time')
    close_time = data.get('close_time')

    if not shop_name or not address or not open_time or not close_time:
        return {
            "success": False,
            "message": "shop_name, address, open_time, close_time required"
        }, 400

    conn = get_db_connection()

    # check existing shop
    existing = conn.execute(
        "SELECT id FROM barber_shops WHERE barber_id=?",
        (barber_id,)
    ).fetchone()

    if existing:
        conn.close()
        return {"success": False, "message": "Shop already exists"}, 409

    # insert shop
    conn.execute(
        "INSERT INTO barber_shops (barber_id, shop_name, address, open_time, close_time) VALUES (?, ?, ?, ?, ?)",
        (barber_id, shop_name, address, open_time, close_time)
    )

    conn.commit()
    conn.close()

    return {"success": True, "message": "Shop created successfully"}, 201


@app.route('/api/service', methods=['POST'])
@token_required(role="barber")
def api_add_service():
    data = request.get_json()

    if not data:
        return {"success": False, "message": "JSON body required"}, 400

    shop_id = data.get('shop_id')
    name = data.get('name')
    price = data.get('price')
    duration = data.get('duration')

    if not shop_id or not name or not price or not duration:
        return {
            "success": False,
            "message": "shop_id, name, price, duration required"
        }, 400

    conn = get_db_connection()                  
    barber_id = request.user["user_id"]            


    shop = conn.execute(
        "SELECT id FROM barber_shops WHERE id=? AND barber_id=?",
        (shop_id, barber_id)
    ).fetchone()

    if not shop:
        conn.close()
        return {"success": False, "message": "Unauthorized shop"}, 403

    conn.execute(
        "INSERT INTO services (shop_id, name, price, duration) VALUES (?, ?, ?, ?)",
        (shop_id, name, price, duration)
    )

    conn.commit()
    conn.close()

    return {"success": True, "message": "Service created successfully"}, 201



@app.route('/api/cancel-booking', methods=['POST'])
@token_required(role="customer")
def cancel_booking():
    booking_id = request.get_json().get("booking_id")
    user_id = request.user["user_id"]

    conn = get_db_connection()

    booking = conn.execute(
        "SELECT * FROM bookings WHERE id=? AND user_id=? AND status='booked'",
        (booking_id, user_id)
    ).fetchone()

    if not booking:
        conn.close()
        return {"success": False, "message": "Invalid booking"}, 404

    conn.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (booking_id,))
    conn.execute("UPDATE slots SET is_available=1 WHERE id=?", (booking["slot_id"],))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Booking cancelled"}

@app.route('/api/generate-slots', methods=['POST'])
@token_required(role="barber")
def api_generate_slots():
    data = request.get_json()

    if not data:
        return {"success": False, "message": "JSON body required"}, 400

    service_id = data.get('service_id')
    if not service_id:
        return {"success": False, "message": "service_id required"}, 400

    conn = get_db_connection()  

    service = conn.execute(
        "SELECT * FROM services WHERE id = ?",
        (service_id,)
    ).fetchone()

    if service is None:
        conn.close()
        return {"success": False, "message": "Service not found"}, 404

    barber = conn.execute("""
    SELECT barber_shops.barber_id
    FROM services
    JOIN barber_shops ON services.shop_id = barber_shops.id
    WHERE services.id = ?
""", (service_id,)).fetchone()

    if not barber:
        conn.close()
        return {"success": False, "message": "Unauthorized"}, 403

    if barber["barber_id"] != request.user["user_id"]:
        conn.close()
        return {"success": False, "message": "Unauthorized"}, 403


    today = datetime.today().strftime("%Y-%m-%d")

    conn.execute(
        "DELETE FROM slots WHERE service_id = ? AND date = ?",
        (service_id, today)
    )

    # shop timing fetch karo
    shop = conn.execute("""
    SELECT barber_shops.open_time, barber_shops.close_time
    FROM services
    JOIN barber_shops ON services.shop_id = barber_shops.id
    WHERE services.id = ?
""", (service_id,)).fetchone()

    if not shop:
        conn.close()
        return {"success": False, "message": "Shop not found"}, 404

    start_time = datetime.strptime(shop["open_time"], "%H:%M")
    end_time = datetime.strptime(shop["close_time"], "%H:%M")

    duration = int(service['duration'])

    current = start_time
    while current + timedelta(minutes=duration) <= end_time:
        conn.execute(
            """INSERT INTO slots
               (service_id, date, start_time, end_time, is_available)
               VALUES (?, ?, ?, ?, 1)""",
            (
                service_id,
                today,
                current.strftime("%H:%M"),
                (current + timedelta(minutes=duration)).strftime("%H:%M")
            )
        )
        current += timedelta(minutes=duration)

    conn.commit()
    conn.close()

    return {"success": True, "message": "Slots generated successfully"}, 201

@app.route('/api/slots/<int:service_id>', methods=['GET'])
@token_required(role="customer")
def api_view_slots(service_id):
    conn = get_db_connection()

    slots = conn.execute("""
        SELECT id, date, start_time, end_time
        FROM slots
        WHERE service_id = ? AND is_available = 1
    """, (service_id,)).fetchall()

    conn.close()

    if not slots:
        return {
            "success": False,
            "message": "No available slots"
        }, 404

    return {
        "success": True,
        "slots": [
            {
                "slot_id": s["id"],
                "date": s["date"],
                "start_time": s["start_time"],
                "end_time": s["end_time"]
            }
            for s in slots
        ]
    }

@app.route('/api/book-slot', methods=['POST'])
@token_required(role="customer")
def api_book_slot():
    data = request.get_json()

    if not data:
        return {"success": False, "message": "JSON body required"}, 400

    user_id = request.user["user_id"]
    slot_id = data.get('slot_id')

    if not user_id or not slot_id:
        return {
            "success": False,
            "message": "user_id and slot_id required"
        }, 400

    conn = get_db_connection()

   
    slot = conn.execute(
        "SELECT * FROM slots WHERE id = ? AND is_available = 1",
        (slot_id,)
    ).fetchone()

    if slot is None:
        conn.close()
        return {
            "success": False,
            "message": "Slot already booked"
        }, 409

    conn.execute(
        "INSERT INTO bookings (user_id, slot_id, status) VALUES (?, ?, ?)",
        (user_id, slot_id, "booked")
    )


    conn.execute(
        "UPDATE slots SET is_available = 0 WHERE id = ?",
        (slot_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Slot booked successfully"
    }, 201

if __name__ == '__main__':
    app.run(debug=True)
