from werkzeug.security import generate_password_hash,check_password_hash
from flask_cors import CORS
from contextlib import contextmanager
from datetime import datetime, timedelta
from Backend.db import get_db_connection
from Backend.create_tables import create_tables
from flask import Flask, request, jsonify, make_response
import os
import jwt
from functools import wraps
from dotenv import load_dotenv
load_dotenv()

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
JWT_ACCESS_SECRET = os.getenv("JWT_ACCESS_SECRET")
JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET")

if not FLASK_SECRET_KEY:
    raise Exception("Missing FLASK_SECRET_KEY in .env")
if not JWT_ACCESS_SECRET or not JWT_REFRESH_SECRET:
    raise Exception("JWT secrets missing in .env file")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL missing in .env")



app = Flask(__name__)

with app.app_context():
    print("✅ Checking database tables...")
    create_tables()

CORS(
    app,
    resources={r"/api/*": {
        "origins": ["https://barber-shop-booking-system-staticsite.onrender.com"]
    }},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

app.secret_key = FLASK_SECRET_KEY

@contextmanager
def get_cursor():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    finally:
        conn.close()

def generate_access_token(user):
    payload = {
        "user_id": user["id"],
        "role": user["role"],
        "exp": datetime.utcnow() + timedelta(hours=6)
    }
    return jwt.encode(payload, JWT_ACCESS_SECRET, algorithm="HS256")

def generate_refresh_token(user):
    payload = {
        "user_id": user["id"],
        "role": user["role"],
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_REFRESH_SECRET, algorithm="HS256")

@app.route("/logout", methods=["POST"])
def logout():
    response = make_response({
        "success": True,
        "message": "Logged out successfully"
    })

    is_production = os.getenv("FLASK_ENV") == "production"

    response.set_cookie(
        "refresh_token",
        "",
        expires=0,
        httponly=True,
        secure=is_production,
        samesite="None" if is_production else "Lax"
    )

    return response




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


@app.route("/refresh", methods=["POST"])
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
        "exp": datetime.utcnow() + timedelta(hours=6)
    },
            JWT_ACCESS_SECRET,
            algorithm="HS256"
)

        return jsonify({
    "success": True,
    "access_token": new_access
})

    except jwt.ExpiredSignatureError:
        return {"message": "Refresh expired"}, 401

    except jwt.InvalidTokenError:
        return {"message": "Invalid refresh token"}, 401

@app.route('/signup', methods=['POST'])
def api_signup():
    try:
        data = request.get_json()

        name = data.get('name')
        phone = data.get('phone')
        raw_password = data.get('password')
        role = data.get('role')

        shop_name = data.get('shop_name')
        address = data.get('address')
        open_time = data.get('open_time')
        close_time = data.get('close_time')

        if not name or not phone or not raw_password or not role:
            return {"success": False, "message": "Missing fields"}, 400

        password = generate_password_hash(raw_password)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if phone exists
        cursor.execute("SELECT id FROM users WHERE phone=%s", (phone,))
        existing = cursor.fetchone()

        if existing:
            conn.close()
            return {"success": False, "message": "Phone already registered"}, 409

        # 🔹 Step 1: Insert user
        cursor.execute(
            "INSERT INTO users (name, phone, password, role) VALUES (%s, %s, %s, %s) RETURNING id",
            (name, phone, password, role)
        )

        user = cursor.fetchone()
        user_id = user["id"]

        # 🔹 Step 2: If barber → create shop automatically
        capacity = data.get("capacity")

        if role == "barber":
            cursor.execute(
            """INSERT INTO barber_shops
            (barber_id, shop_name, address, open_time, close_time, capacity)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
        (user_id, shop_name, address, open_time, close_time, capacity)
    )

        conn.commit()
        conn.close()

        return {"success": True, "message": "User created successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}, 500

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
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


@app.route("/services", methods=["GET"])
@token_required()
def get_services():

    role = request.user["role"]
    user_id = request.user["user_id"]

    with get_cursor() as cursor:

        if role == "barber":
            cursor.execute("""
                SELECT services.id, services.name, services.price, services.duration
                FROM services
                JOIN barber_shops ON services.shop_id = barber_shops.id
                WHERE barber_shops.barber_id = %s
            """, (user_id,))
        else:
            cursor.execute(
                "SELECT id, name, price, duration FROM services"
            )

        services = [dict(s) for s in cursor.fetchall()]

    return jsonify({
        "success": True,
        "services": services
    })
@app.route("/shops", methods=["GET"])
@token_required(role="customer")
def get_shops():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, shop_name, address
        FROM barber_shops
    """)

    shops = cursor.fetchall()
    conn.close()

    return {"shops": shops}

@app.route("/shop-services/<int:shop_id>", methods=["GET"])
@token_required(role="customer")
def get_shop_services(shop_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, price, duration
        FROM services
        WHERE shop_id = %s
    """, (shop_id,))

    services = cursor.fetchall()
    conn.close()

    return {"services": services}

@app.route('/service', methods=['POST'])
@token_required(role="barber")
def api_add_service():

    data = request.get_json()
    if not data:
        return {"success": False, "message": "JSON body required"}, 400

    name = data.get("name")
    price = data.get("price")
    duration = data.get("duration")

    barber_id = request.user["user_id"]

    with get_cursor() as cursor:

        # 🔹 Get barber's shop automatically
        cursor.execute(
            "SELECT id FROM barber_shops WHERE barber_id=%s",
            (barber_id,)
        )

        shop = cursor.fetchone()

        if not shop:
            return {"success": False, "message": "Shop not found"}, 404

        shop_id = shop["id"]

        # 🔹 Insert service
        cursor.execute("""
            INSERT INTO services (shop_id, name, price, duration)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (shop_id, name, price, duration))

        service_id = cursor.fetchone()["id"]

    return {
        "success": True,
        "message": "Service created successfully",
        "service": {
            "id": service_id,
            "name": name,
            "price": price,
            "duration": duration
        }
    }, 201

@app.route('/generate-slots', methods=['POST'])
@token_required(role="barber")
def api_generate_slots():

    data = request.get_json()

    if not data:
        return {"success": False, "message": "JSON body required"}, 400

    service_id = data.get("service_id")
    if not service_id:
        return {"success": False, "message": "service_id required"}, 400

    with get_cursor() as cursor:

        # ✅ get service
        cursor.execute(
            "SELECT * FROM services WHERE id=%s",
            (service_id,)
        )
        service = cursor.fetchone()

        if not service:
            return {"success": False, "message": "Service not found"}, 404

        # ✅ verify barber ownership
        cursor.execute("""
           SELECT barber_shops.barber_id,
                barber_shops.open_time,
                barber_shops.close_time,
                barber_shops.capacity
            FROM services
            JOIN barber_shops ON services.shop_id = barber_shops.id
            WHERE services.id=%s
        """, (service_id,))

    shop = cursor.fetchone()

    duration = service["duration"]
    capacity = shop.get("capacity", 1)

    today = datetime.today().date()

    start_time = datetime.strptime(shop["open_time"], "%H:%M")
    end_time = datetime.strptime(shop["close_time"], "%H:%M")
    current = start_time

    while current + timedelta(minutes=duration) <= end_time:

        for i in range(int(capacity)):

            cursor.execute("""
            INSERT INTO slots
            (service_id,date,start_time,end_time,is_available)
            VALUES (%s,%s,%s,%s,1)
        """, (
            service_id,
            today,
            current.strftime("%H:%M"),
            (current + timedelta(minutes=duration)).strftime("%H:%M")
        ))

    current += timedelta(minutes=duration)

    return {"success": True, "message": "Slots generated for today"}

@app.route('/slots/<int:service_id>', methods=['GET'])
@token_required(role="customer")
def api_view_slots(service_id):
    with get_cursor() as cursor:

        cursor.execute("""
            SELECT id,date,start_time,end_time
            FROM slots
            WHERE service_id=%s AND is_available=1
    """,(service_id,))

        slots = cursor.fetchall()

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

@app.route("/service/<int:service_id>", methods=["PUT"])
@token_required(role="barber")
def update_service(service_id):

    data = request.get_json()
    if not data:
        return {"success": False, "message": "JSON body required"}, 400

    name = data.get("name")
    price = data.get("price")
    duration = data.get("duration")

    barber_id = request.user["user_id"]

    with get_cursor() as cursor:

        cursor.execute("""
            SELECT services.id
            FROM services
            JOIN barber_shops ON services.shop_id = barber_shops.id
            WHERE services.id=%s AND barber_shops.barber_id=%s
        """, (service_id, barber_id))

        if not cursor.fetchone():
            return {"success": False, "message": "Unauthorized"}, 403

        cursor.execute("""
            UPDATE services
            SET name=%s, price=%s, duration=%s
            WHERE id=%s
        """, (name, price, duration, service_id))

    return {"success": True, "message": "Service updated"}

@app.route("/service/<int:service_id>", methods=["DELETE"])
@token_required(role="barber")
def delete_service(service_id):

    barber_id = request.user["user_id"]

    with get_cursor() as cursor:

        cursor.execute("""
            DELETE FROM services
            USING barber_shops
            WHERE services.shop_id = barber_shops.id
            AND services.id=%s
            AND barber_shops.barber_id=%s
        """, (service_id, barber_id))

        if cursor.rowcount == 0:
            return {"success": False, "message": "Unauthorized"}, 403

    return {"success": True, "message": "Service deleted"}

@app.route("/shop", methods=["GET"])
@token_required(role="barber")
def get_shop():

    barber_id = request.user["user_id"]

    with get_cursor() as cursor:

        cursor.execute(
            "SELECT * FROM barber_shops WHERE barber_id=%s",
            (barber_id,)
        )
        shop = cursor.fetchone()
        if not shop:
            return {"success": False, "message": "Shop not found"}, 404

    return {"success": True, "shop": dict(shop)}
    
@app.route("/barber-bookings", methods=["GET"])
@token_required(role="barber")
def barber_bookings():

    barber_id = request.user["user_id"]

    with get_cursor() as cursor:

        cursor.execute("""
            SELECT 
                bookings.id AS booking_id,
                bookings.status,
                users.name AS customer_name,
                slots.date,
                slots.start_time,
                slots.end_time,
                services.name AS service_name
            FROM bookings
            JOIN slots ON bookings.slot_id = slots.id
            JOIN services ON slots.service_id = services.id
            JOIN barber_shops ON services.shop_id = barber_shops.id
            JOIN users ON bookings.user_id = users.id
            WHERE barber_shops.barber_id = %s
        """, (barber_id,))

        data = [dict(d) for d in cursor.fetchall()]

    return {"success": True, "bookings": data}

@app.route("/my-shop", methods=["GET"])
@token_required
def get_my_shop(current_user):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, shop_name FROM shops WHERE barber_id = %s",
        (current_user["id"],)
    )

    shop = cursor.fetchone()

    cursor.close()
    conn.close()

    if shop:
        return jsonify({
            "success": True,
            "shop_id": shop[0],
            "shop_name": shop[1]
        })
    else:
        return jsonify({
            "success": False,
            "message": "Shop not found"
        }), 404

@app.route('/my-bookings', methods=['GET'])
@token_required(role="customer")
def my_bookings():

    user_id = request.user["user_id"]

    with get_cursor() as cursor:

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

        bookings = [dict(b) for b in cursor.fetchall()]

    return {"success": True, "bookings": bookings}

@app.route('/cancel-booking', methods=['POST'])
@token_required(role="customer")
def cancel_booking():

    data = request.get_json()
    if not data:
        return {"success": False, "message": "JSON body required"}, 400

    booking_id = data.get("booking_id")
    user_id = request.user["user_id"]

    with get_cursor() as cursor:

        cursor.execute(
            "SELECT slot_id FROM bookings WHERE id=%s AND user_id=%s",
            (booking_id, user_id)
        )

        booking = cursor.fetchone()

        if not booking:
            return {"success": False, "message": "Invalid booking"}, 404

        cursor.execute(
            "UPDATE bookings SET status='cancelled' WHERE id=%s",
            (booking_id,)
        )

        cursor.execute(
            "UPDATE slots SET is_available=1 WHERE id=%s",
            (booking["slot_id"],)
        )

    return {"success": True, "message": "Booking cancelled"}

@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


