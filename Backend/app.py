from flask import Flask, request
from flask_cors import CORS
from datetime import datetime, timedelta
import sqlite3
import time
import os
import jwt
from functools import wraps


app = Flask (__name__)
app.secret_key = "my_super_secret_key_123"

JWT_SECRET = "super_jwt_secret_key"

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
    data = request.get_json()

    if not data or "phone" not in data:
        return {"success": False, "message": "Phone required"}, 400

    phone = data.get("phone")

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE phone = ?",
        (phone,)
    ).fetchone()
    conn.close()

    if user is None:
        return {
            "success": False,
            "message": "User not found"
        }, 404

    token = generate_token(user)

    return {
        "success": True,
        "token": token
    }, 200


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_db_connection():
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'database.db'))
    conn.row_factory = sqlite3.Row 
    return conn

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json()

    if not data:
        return {"success": False, "message": "JSON body required"}, 400

    name = data.get('name')
    phone = data.get('phone')
    role = data.get('role')

    if not name or not phone or not role:
        return {"success": False, "message": "name, phone, role required"}, 400

    conn = get_db_connection()

    existing = conn.execute(
        "SELECT id FROM users WHERE phone = ?",
        (phone,)
    ).fetchone()

    if existing:
        conn.close()
        return {"success": False, "message": "Phone already registered"}, 409

    conn.execute(
        "INSERT INTO users (name, phone, role) VALUES (?, ?, ?)",
        (name, phone, role)
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "User created successfully"}, 201


@app.route('/api/shop', methods=['POST'])
@token_required(role="barber")
def api_add_shop():
    data = request.get_json()

    if not data:
        return {"success": False, "message": "JSON body required"}, 400

    barber_id = request.user["user_id"]
    shop_name = data.get('shop_name')
    address = data.get('address')

    if not shop_name or not address:
        return {
            "success": False,
            "message": "shop_name and address required"
        }, 400

    conn = get_db_connection()

    # 🔒 OPTIONAL BUT RECOMMENDED FIX (HERE 👇)
    existing = conn.execute(
        "SELECT id FROM barber_shops WHERE barber_id = ?",
        (barber_id,)
    ).fetchone()

    if existing:
        conn.close()
        return {
            "success": False,
            "message": "Shop already exists for this barber"
        }, 409

    # ✅ SAFE INSERT
    conn.execute(
        "INSERT INTO barber_shops (barber_id, shop_name, address) VALUES (?, ?, ?)",
        (barber_id, shop_name, address)
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

    start_time = datetime.strptime("09:00", "%H:%M")
    end_time = datetime.strptime("12:00", "%H:%M")
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
