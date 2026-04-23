import os
import random
import requests as http_requests
from datetime import datetime
from flask import Flask, request, jsonify, render_template, Response
from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client

app = Flask(__name__)

# Google Places API Key (server-side only, never sent to browser)
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")

# Twilio Config
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_VERIFY_SERVICE_SID = os.environ.get("TWILIO_VERIFY_SERVICE_SID", "")
USE_TWILIO = True # Twilio Verify enabled — live OTP SMS active
TWILIO_FROM_NUMBER = "+15075555555"  # ← Replace with your Twilio number from console.twilio.com

# Database config
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'resqnow.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-resqnow-key')

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100))
    age = db.Column(db.String(10))
    relationship = db.Column(db.String(50))
    allergies = db.Column(db.Text)
    chronic_conditions = db.Column(db.Text)
    medications = db.Column(db.Text)
    surgical_history = db.Column(db.Text)

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    distance_km = db.Column(db.Float)
    drive_time_mins = db.Column(db.Integer)
    specialist_on_call = db.Column(db.String(100))
    admission_fee = db.Column(db.Float)
    ambulance_charge = db.Column(db.Float)
    status = db.Column(db.String(20)) # ACTIVE, STANDBY, BUSY
    db_type = db.Column(db.String(20)) # Government, Private
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)

class EmergencyRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emergency_type = db.Column(db.String(50))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    status = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class BookingHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100))
    emergency_type = db.Column(db.String(50))
    hospital_name = db.Column(db.String(150))
    service_request_no = db.Column(db.String(50))
    driver_name = db.Column(db.String(100))
    vehicle_number = db.Column(db.String(50))
    status = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

def seed_hospitals():
    if Hospital.query.first():
        return
    hospitals = [
        {"name": "City General Medical Center", "distance_km": 2.4, "drive_time_mins": 8, "specialist_on_call": "Trauma Surgeon Available", "admission_fee": 150.00, "ambulance_charge": 50.00, "status": "ACTIVE", "db_type": "Government", "lat": 40.7128, "lng": -74.0060},
        {"name": "Hope Wellness Clinic", "distance_km": 4.1, "drive_time_mins": 12, "specialist_on_call": "Cardiologist arriving in 15m", "admission_fee": 120.00, "ambulance_charge": 40.00, "status": "STANDBY", "db_type": "Private", "lat": 40.7300, "lng": -74.0100},
        {"name": "St. Jude Medical", "distance_km": 5.8, "drive_time_mins": 18, "specialist_on_call": "Neurosurgeon On-Duty", "admission_fee": 200.00, "ambulance_charge": 60.00, "status": "ACTIVE", "db_type": "Private", "lat": 40.7400, "lng": -74.0200},
        {"name": "Valley Health Center", "distance_km": 6.2, "drive_time_mins": 20, "specialist_on_call": "ER Specialist On-Duty", "admission_fee": 110.00, "ambulance_charge": 35.00, "status": "ACTIVE", "db_type": "Government", "lat": 40.7500, "lng": -74.0300},
        {"name": "Unity Care Hospital", "distance_km": 7.5, "drive_time_mins": 25, "specialist_on_call": "Staff Shift Change in 10m", "admission_fee": 140.00, "ambulance_charge": 55.00, "status": "BUSY", "db_type": "Private", "lat": 40.7600, "lng": -74.0400},
        {"name": "Beacon Medical", "distance_km": 8.9, "drive_time_mins": 30, "specialist_on_call": "Multi-Specialist Team", "admission_fee": 180.00, "ambulance_charge": 70.00, "status": "ACTIVE", "db_type": "Private", "lat": 40.7700, "lng": -74.0500}
    ]
    for h_data in hospitals:
        h = Hospital(**h_data)
        db.session.add(h)
    db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

# --- API Endpoints ---

@app.route('/api/auth/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    phone = data.get('phone', '').strip()
    if not phone:
        return jsonify({"error": "Phone required"}), 400

    # Normalize to E.164 format
    if not phone.startswith('+'):
        phone = '+91' + phone.lstrip('0')

    if USE_TWILIO:
        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            verification = client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID) \
                                          .verifications \
                                          .create(to=phone, channel='sms')
            return jsonify({"success": True, "message": "OTP sent via Twilio.", "status": verification.status})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Twilio Error", "details": str(e)}), 500
    else:
        # MOCK MODE
        print(f"\n" + "="*40)
        print(f"📲 [MOCK MODE] OTP triggered for {phone}")
        print(f"📢 (Twilio disabled. Use 123456 to verify in mock mode)")
        print("="*40 + "\n")
        return jsonify({"success": True, "message": "Mock OTP triggered."})

@app.route('/api/auth/verify', methods=['POST'])
def verify_otp():
    data = request.json
    phone = data.get('phone')
    otp = data.get('otp')
    
    if not phone or not otp:
        return jsonify({"error": "Phone and OTP required"}), 400

    if USE_TWILIO:
        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            verification_check = client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID) \
                                               .verification_checks \
                                               .create(to=phone, code=otp)
            
            if verification_check.status == 'approved':
                # Check for existing user or create
                user = User.query.filter_by(phone=phone).first()
                if not user:
                    user = User(phone=phone)
                    db.session.add(user)
                    db.session.commit()
                return jsonify({"success": True, "user_id": user.id})
            else:
                return jsonify({"error": "Invalid OTP", "status": verification_check.status}), 401
        except Exception as e:
            return jsonify({"error": "Twilio Verification Error", "details": str(e)}), 500
    else:
        # MOCK MODE
        if otp == "123456":
            user = User.query.filter_by(phone=phone).first()
            if not user:
                user = User(phone=phone)
                db.session.add(user)
                db.session.commit()
            return jsonify({"success": True, "user_id": user.id})
        return jsonify({"error": "Invalid Mock OTP"}), 401

@app.route('/api/notify/dispatched', methods=['POST'])
def notify_dispatched():
    """Send a WhatsApp message to the patient when the ambulance is dispatched."""
    data = request.json or {}
    to_phone    = data.get('phone', '+918790889527')
    hospital    = data.get('hospital', 'the hospital')
    driver       = data.get('driver', 'your driver')
    driver_phone = data.get('driverPhone', '')
    booking_ref  = data.get('bookingRef', '')
    eta_mins     = data.get('eta', '?')

    driver_contact = f"+91 {driver_phone[:5]}*****" if driver_phone else 'on the way'

    message_body = (
        f"🚑 *ResQNow — Ambulance Dispatched!*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Your ambulance has been dispatched and is en route to you.\n\n"
        f"📋 *Tracking ID:* {booking_ref}\n"
        f"⏱️ *Est. Arrival:* {eta_mins} min\n"
        f"🏥 *Hospital:* {hospital}\n\n"
        f"🧑‍✈️ *Driver Details*\n"
        f"   Name: {driver}\n"
        f"   Contact: {driver_contact}\n\n"
        f"_Please be ready at your location._\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"ResQNow Emergency Services"
    )

    if USE_TWILIO:
        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            # Ensure E.164 format
            if not to_phone.startswith('+'):
                to_phone = '+91' + to_phone.lstrip('0')
            msg = client.messages.create(
                body=message_body,
                from_='whatsapp:+14155238886',   # Twilio WhatsApp Sandbox number
                to=f'whatsapp:{to_phone}'
            )
            print(f"📲 Dispatch WhatsApp sent to {to_phone} — SID: {msg.sid}")
            return jsonify({"success": True, "sid": msg.sid})
        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    else:
        print(f"📲 [MOCK] Dispatch WhatsApp to {to_phone}:\n{message_body}")
        return jsonify({"success": True, "mock": True})

@app.route('/api/profile/<int:user_id>', methods=['POST'])
def save_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    data = request.json
    user.name = data.get('name')
    user.age = data.get('age')
    user.relationship = data.get('relationship')
    user.allergies = data.get('allergies')
    user.chronic_conditions = data.get('chronic_conditions')
    user.medications = str(data.get('medications')) # Store as string for simplicity
    user.surgical_history = data.get('surgical_history')
    
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "name": user.name,
        "phone": user.phone,
        "age": user.age,
        "relationship": user.relationship,
        "allergies": user.allergies,
        "chronic_conditions": user.chronic_conditions,
        "medications": user.medications,
        "surgical_history": user.surgical_history
    })

@app.route('/api/history/<int:user_id>', methods=['GET'])
def get_booking_history(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    history = BookingHistory.query.filter_by(user_name=user.name) \
        .order_by(BookingHistory.timestamp.desc()) \
        .all()

    return jsonify([
        {
            "id": item.id,
            "user_name": item.user_name,
            "emergency_type": item.emergency_type,
            "hospital_name": item.hospital_name,
            "service_request_no": item.service_request_no,
            "driver_name": item.driver_name,
            "vehicle_number": item.vehicle_number,
            "status": item.status,
            "timestamp": item.timestamp.isoformat() if item.timestamp else None
        }
        for item in history
    ])

@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    hospitals = Hospital.query.order_by(Hospital.distance_km).all()
    res = []
    for h in hospitals:
        res.append({
            "id": h.id,
            "name": h.name,
            "distance_km": h.distance_km,
            "drive_time_mins": h.drive_time_mins,
            "specialist_on_call": h.specialist_on_call,
            "admission_fee": h.admission_fee,
            "ambulance_charge": h.ambulance_charge,
            "status": h.status,
            "type": h.db_type,
            "lat": h.lat,
            "lng": h.lng
        })
    return jsonify(res)

@app.route('/api/hospitals/clear', methods=['POST'])
def clear_hospitals():
    cleared_requests = db.session.query(EmergencyRequest).delete(synchronize_session=False)
    deleted = db.session.query(Hospital).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({
        "success": True,
        "deleted_hospitals": deleted,
        "deleted_requests": cleared_requests
    })

@app.route('/api/dispatch', methods=['POST'])
def dispatch_help():
    data = request.json
    user_id = data.get('user_id')
    emergency_type = data.get('emergency_type')
    lat = data.get('lat')
    lng = data.get('lng')
    hospital_id = data.get('hospital_id')
    hospital_name = data.get('hospital_name')
    service_request_no = data.get('service_request_no')
    driver_name = data.get('driver_name')
    vehicle_number = data.get('vehicle_number')
    user = User.query.get(user_id)
    user_name = user.name if user else None

    if not hospital_name and hospital_id:
        hospital = Hospital.query.filter_by(id=hospital_id).first()
        if hospital:
            hospital_name = hospital.name
    
    req = EmergencyRequest(
        emergency_type=emergency_type,
        lat=lat,
        lng=lng,
        status="Dispatched"
    )

    booking = BookingHistory(
        user_name=user_name,
        emergency_type=emergency_type,
        hospital_name=hospital_name,
        service_request_no=service_request_no,
        driver_name=driver_name,
        vehicle_number=vehicle_number,
        status="Dispatched"
    )

    db.session.add(req)
    db.session.add(booking)
    db.session.commit()
    return jsonify({"success": True, "request_id": req.id, "booking_id": booking.id})

@app.route('/api/places', methods=['GET'])
def search_places():
    query = request.args.get('query', '').strip()
    lat   = request.args.get('lat', '')
    lng   = request.args.get('lng', '')
    if not query:
        return jsonify({"error": "Query required"}), 400

    # ── Places API (New) ── POST /v1/places:searchText
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,"
            "places.rating,places.userRatingCount,places.currentOpeningHours,"
            "places.location,places.photos,places.primaryTypeDisplayName"
        )
    }
    body = {"textQuery": query + " hospital"}
    if lat and lng:
        body["locationBias"] = {
            "circle": {
                "center": {"latitude": float(lat), "longitude": float(lng)},
                "radius": 10000.0
            }
        }

    try:
        resp = http_requests.post(url, json=body, headers=headers, timeout=10)
        data = resp.json()

        if "error" in data:
            return jsonify({"error": data["error"].get("message", "API error")}), 500

        results = []
        for place in data.get("places", [])[:5]:
            loc     = place.get("location", {})
            oh      = place.get("currentOpeningHours", {})
            photos  = place.get("photos", [])
            name    = place.get("displayName", {}).get("text", "Unknown")
            ptype   = place.get("primaryTypeDisplayName", {}).get("text", "Hospital")
            photo_name = photos[0].get("name", "") if photos else ""
            results.append({
                "id":       place.get("id"),
                "name":     name,
                "address":  place.get("formattedAddress", ""),
                "rating":   place.get("rating"),
                "reviews":  place.get("userRatingCount", 0),
                "isOpen":   oh.get("openNow", True),
                "status":   "Open now" if oh.get("openNow", True) else "Closed",
                "lat":      loc.get("latitude"),
                "lng":      loc.get("longitude"),
                "type":     ptype,
                "photo_name": photo_name
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/places/photo', methods=['GET'])
def get_place_photo():
    name = request.args.get('name', '')
    if not name:
        return '', 400
    url = f"https://places.googleapis.com/v1/{name}/media?maxWidthPx=400&key={GOOGLE_PLACES_API_KEY}"
    resp = http_requests.get(url, timeout=10)
    return Response(resp.content, content_type=resp.headers.get('Content-Type', 'image/jpeg'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_hospitals()
    app.run(host='0.0.0.0', debug=True, port=8080)
