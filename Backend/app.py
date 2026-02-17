from werkzeug.security import generate_password_hash,check_password_hash
from flask_cors import CORS
from datetime import datetime, timedelta
from Backend.db import get_db_connection
from Backend.create_tables import create_tables
from flask import Flask, request, jsonify, make_response
import os
import jwt
from functools import wraps
from dotenv import load_dotenv
load_dotenv()



FLASK_SECRET_KEY = os.getenv("my_flask_secret_456")
JWT_ACCESS_SECRET = os.getenv("access_secret_key")
JWT_REFRESH_SECRET = os.getenv("refresh_secret_key")

print("ACCESS:", os.getenv("JWT_ACCESS_SECRET"))
print("REFRESH:", os.getenv("JWT_REFRESH_SECRET"))

if not FLASK_SECRET_KEY:
    raise Exception("Missing FLASK_SECRET_KEY in .env")

if not JWT_ACCESS_SECRET or not JWT_REFRESH_SECRET:
    raise Exception("JWT secrets missing in .env file")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL missing in .env")



app = Flask (__name__)

if os.getenv("FLASK_ENV") == "development":
    create_tables()

app.secret_key = FLASK_SECRET_KEY

CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:3000",
        "https://barber-shop-booking-system.onrender.com"
    ]
)




def generate_access_token(user):
    payload = {
        "user_id": user["id"],
        "role": user["role"],
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }
    return jwt.encode(payload, JWT_ACCESS_SECRET, algorithm="HS256")



def generate_refresh_token(user):
    payload = {
    "user_id": user["id"],
    "role": user["role"],
    "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_REFRESH_SECRET, algorithm="HS256")



def token_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization")

            if not auth:
                return {"success": False, "message": "Token missing"}, 401

            try:
                if not auth.startswith("Bearer "):
                    return {"success": False, "message": "Invalid token format"}, 401

                token = auth.split(" ")[1]

                data = jwt.decode(token, JWT_ACCESS_SECRET, algorithms=["HS256"])


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
@token_required()
def get_services():

    conn = get_db_connection()
    cursor = conn.cursor()

    role = request.user["role"]
    user_id = request.user["user_id"]

    if role == "barber":
        cursor.execute("""
            SELECT services.id, services.name, services.price, services.duration
            FROM services
            JOIN barber_shops ON services.shop_id = barber_shops.id
            WHERE barber_shops.barber_id = %s
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT id, name, price, duration FROM services
        """)

    services = cursor.fetchall()

    conn.close()

    return {"services": services}


@app.route('/api/login', methods=['POST'])
def api_login():
    conn = None
    try:
        data = request.get_json()

        if not data:
            return {"success": False, "message": "JSON body required"}, 400

        phone = data.get("phone")
        password = data.get("password")

        if not phone or not password:
            return {"success": False, "message": "Phone and password required"}, 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE phone = %s",
            (phone,)
        )

        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):

            access_token = generate_access_token(user)
            refresh_token = generate_refresh_token(user)

            response = make_response(jsonify({
                "success": True,
                "access_token": access_token,
                "user": {
                    "id": user["id"],
                    "name": user["name"],
                    "role": user["role"]
                }
            }))

            is_production = os.getenv("FLASK_ENV") == "production"

            response.set_cookie(
                "refresh_token",
                refresh_token,
                httponly=True,
                secure=is_production,
                samesite="None" if is_production else "Lax"
            )

            return response

        return {"success": False, "message": "Invalid credentials"}, 401

    except Exception as e:
        return {"success": False, "error": str(e)}, 500

    finally:
        if conn:
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

        # ✅ Role validation BEFORE insert
        if role not in ["customer", "barber"]:
            return {"success": False, "message": "Invalid role"}, 400

        password = generate_password_hash(raw_password)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
        "SELECT id FROM users WHERE phone=%s",
        (phone,)
)

        existing = cursor.fetchone()


        if existing:
            conn.close()
            return {"success": False, "message": "Phone already registered"}, 409

        cursor.execute(
            "INSERT INTO users (name, phone, password, role) VALUES (%s, %s, %s, %s)",
            (name, phone, password, role)
)


        conn.commit()
        conn.close()

        return {"success": True, "message": "User created successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}, 500



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
    cursor = conn.cursor()

    
    cursor.execute(
        "SELECT id FROM barber_shops WHERE barber_id=%s",
        (barber_id,)
    )
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return {"success": False, "message": "Shop already exists"}, 409

    

    cursor.execute(
        "INSERT INTO barber_shops (barber_id, shop_name, address, open_time, close_time) VALUES (%s, %s, %s, %s, %s)",
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
    cursor = conn.cursor()                 
    barber_id = request.user["user_id"]            



    cursor.execute(
    "SELECT id FROM barber_shops WHERE id=%s AND barber_id=%s",
    (shop_id, barber_id)
)
    shop = cursor.fetchone()

    if not shop:
        conn.close()
        return {"success": False, "message": "Unauthorized shop"}, 403

    cursor.execute(
        "INSERT INTO services (shop_id, name, price, duration) VALUES (%s, %s, %s, %s)",
        (shop_id, name, price, duration)
    )

    conn.commit()
    conn.close()

    return {"success": True, "message": "Service created successfully"}, 201

@app.route('/api/my-bookings', methods=['GET'])
@token_required(role="customer")
def my_bookings():

    user_id = request.user["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT 
            bookings.id AS booking_id,
            bookings.status,
            slots.date,
            slots.start_time,
            slots.end_time,
            services.name AS service_name,
            barber_shops.shop_name
        FROM bookings
        JOIN slots ON bookings.slot_id = slots.id
        JOIN services ON slots.service_id = services.id
        JOIN barber_shops ON services.shop_id = barber_shops.id
        WHERE bookings.user_id = %s
    """, (user_id,))

    bookings = cursor.fetchall()

    conn.close()

    return {
        "success": True,
        "bookings": bookings
    }


@app.route('/api/cancel-booking', methods=['POST'])
@token_required(role="customer")
def cancel_booking():

    booking_id = request.get_json().get("booking_id")
    user_id = request.user["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    

    cursor.execute(
        "SELECT slot_id FROM bookings WHERE id=%s AND user_id=%s",
        (booking_id, user_id)
    )

    booking = cursor.fetchone()

    if not booking:
        conn.close()
        return {"success": False, "message": "Invalid booking"}, 404

    cursor.execute(
        "UPDATE bookings SET status='cancelled' WHERE id=%s",
        (booking_id,)
    )

    cursor.execute(
        "UPDATE slots SET is_available = 1 WHERE id=%s",
        (booking["slot_id"],)
    )

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
    cursor = conn.cursor() 

    cursor.execute(
        "SELECT * FROM services WHERE id = %s",
        (service_id,)
    )
    service = cursor.fetchone()

    if service is None:
        conn.close()
        return {"success": False, "message": "Service not found"}, 404

    cursor = conn.cursor()
    cursor.execute("""
    SELECT barber_shops.barber_id
    FROM services
    JOIN barber_shops ON services.shop_id = barber_shops.id
    WHERE services.id = %s
""", (service_id,))
    barber = cursor.fetchone()

    if not barber:
        conn.close()
        return {"success": False, "message": "Unauthorized"}, 403

    if barber["barber_id"] != request.user["user_id"]:
        conn.close()
        return {"success": False, "message": "Unauthorized"}, 403


    today = datetime.utcnow().date()


    cursor.execute(
        "DELETE FROM slots WHERE service_id = %s AND date = %s",
        (service_id, today)
    )

    # shop timing fetch karo
    cursor.execute("""
    SELECT barber_shops.open_time, barber_shops.close_time
    FROM services
    JOIN barber_shops ON services.shop_id = barber_shops.id
    WHERE services.id = %s
""", (service_id,))
    shop = cursor.fetchone()

    if not shop:
        conn.close()
        return {"success": False, "message": "Shop not found"}, 404

    start_time = datetime.strptime(shop["open_time"], "%H:%M")
    end_time = datetime.strptime(shop["close_time"], "%H:%M")

    duration = int(service['duration'])

    current = start_time
    while current + timedelta(minutes=duration) <= end_time:
        cursor.execute(
            """INSERT INTO slots
               (service_id, date, start_time, end_time, is_available)
               VALUES (%s, %s, %s, %s, 1)""",
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
    cursor = conn.cursor()

   
    cursor.execute("""
        SELECT id, date, start_time, end_time
        FROM slots
        WHERE service_id = %s AND is_available = 1
    """, (service_id,))
    slots = cursor.fetchall()

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

    if not slot_id:
        return {"success": False, "message": "slot_id required"}, 400

    conn = get_db_connection()
    cursor = conn.cursor()

    
    cursor.execute(
        "UPDATE slots SET is_available = 0 WHERE id = %s AND is_available = 1",
        (slot_id,)
    )

    if cursor.rowcount == 0:
        conn.close()
        return {
            "success": False,
            "message": "Slot already booked"
        }, 409

    # Insert booking
    cursor.execute(
        "INSERT INTO bookings (user_id, slot_id, status) VALUES (%s, %s, %s)",
        (user_id, slot_id, "booked")
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Slot booked successfully"
    }, 201
    
@app.route("/health")
def health():
    return {"status": "ok"}

@app.route("/api/refresh", methods=["POST"])
def refresh_access_token():

    token = request.cookies.get("refresh_token")

    if not token:
        return {"message": "No refresh token"}, 401

    try:
        data = jwt.decode(
        token,
        JWT_REFRESH_SECRET,
        algorithms=["HS256"]
    )

        new_access = jwt.encode(
{
    "user_id": data["user_id"],
    "role": data["role"],
    "exp": datetime.utcnow() + timedelta(minutes=15)
},
        JWT_ACCESS_SECRET,
        algorithm="HS256"
)



        return {
            "success": True,
            "access_token": new_access
}


    except jwt.ExpiredSignatureError:
        return {"message": "Refresh expired"}, 401

    except jwt.InvalidTokenError:
        return {"message": "Invalid refresh token"}, 401


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


