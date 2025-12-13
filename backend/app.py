# app.py  (Neon + deployment ready)
from dotenv import load_dotenv
load_dotenv()

from flask import (
    Flask, request, jsonify, send_from_directory,
    render_template, session, redirect, url_for
)
from functools import wraps
import os
print("DATABASE_URL =", os.environ.get("DATABASE_URL"))
import base64
import numpy as np
import cv2
import face_recognition
import shutil
import threading
import json
import qrcode
from io import BytesIO
import uuid
from datetime import datetime

# DB: use Neon PostgreSQL
import psycopg2
import psycopg2.extras

# Face model
from face_model import FaceRecognitionModel
from face_utils import aggregate_face_encoding_from_bgr_frames, verify_liveness_from_bgr_frames


# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder='../frontend/static',
    template_folder='../frontend/pages'
)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_super_secret_key_here")

# Neon connection string (set this in Render/Railway/locally)
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require"
)

UPLOAD_FOLDER = os.path.join(BASE_DIR, '..', 'uploads')
PROCESSED_FOLDER = os.path.join(BASE_DIR, '..', 'processed')
EVENTS_DATA_PATH = os.path.join(BASE_DIR, '..', 'events_data.json')
KNOWN_FACES_DATA_PATH = os.path.join(BASE_DIR, 'known_faces.dat')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)


# --- DISABLE CACHING FOR ALL RESPONSES ---
@app.after_request
def add_no_cache_headers(response):
    """Disable caching for all responses to prevent stale content"""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# --- INITIALIZE THE ML MODEL ---
model = FaceRecognitionModel(data_file=KNOWN_FACES_DATA_PATH)


# --- DB HELPER ---
def get_db_connection():
    """
    Connect to Neon PostgreSQL using DATABASE_URL.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as err:
        print(f"DB Error: {err}")
        return None


# --- AUTH GUARD ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('serve_login_page'))
        return f(*args, **kwargs)
    return decorated_function


# --- IMAGE PROCESSING / FACE LEARNING ---
def process_images(event_id):
    """
    For each uploaded image:
    - Detect all faces
    - Learn / update identities in the model
    - Classify image as individual / group and copy into processed folder
    """
    try:
        input_dir = os.path.join(app.config['UPLOAD_FOLDER'], event_id)
        output_dir = os.path.join(app.config['PROCESSED_FOLDER'], event_id)
        os.makedirs(output_dir, exist_ok=True)

        print(f"--- [PROCESS] Starting for event: {event_id} ---")

        for filename in os.listdir(input_dir):
            if (filename.lower().endswith(('.png', '.jpg', '.jpeg'))
                    and not filename.endswith('_qr.png')):

                image_path = os.path.join(input_dir, filename)
                print(f"--- [PROCESS] Image: {filename}")

                try:
                    image = face_recognition.load_image_file(image_path)
                    face_encodings = face_recognition.face_encodings(image)
                    print(f"--- [PROCESS] Found {len(face_encodings)} face(s) in {filename}")

                    # Learn / update all faces in this photo
                    person_ids_in_image = set()
                    for encoding in face_encodings:
                        person_id = model.learn_face(encoding)
                        if person_id:
                            person_ids_in_image.add(person_id)

                    # Organize photos into individual / group per person
                    if face_encodings:
                        for pid in person_ids_in_image:
                            person_dir = os.path.join(output_dir, pid)
                            indiv_dir = os.path.join(person_dir, "individual")
                            group_dir = os.path.join(person_dir, "group")
                            os.makedirs(indiv_dir, exist_ok=True)
                            os.makedirs(group_dir, exist_ok=True)

                            if len(face_encodings) == 1:
                                # Individual photo
                                shutil.copy(
                                    image_path,
                                    os.path.join(indiv_dir, filename)
                                )
                            else:
                                # Group photo (add watermarked_ prefix)
                                shutil.copy(
                                    image_path,
                                    os.path.join(group_dir, f"watermarked_{filename}")
                                )

                except Exception as e:
                    print(f"  -> ERROR processing {filename}: {e}")

        print(f"--- [PROCESS] Finished for event: {event_id} ---")

    except Exception as e:
        print(f"  -> FATAL ERROR during processing for event {event_id}: {e}")


# --- PAGE ROUTES ---
@app.route('/')
def serve_index():
    return render_template('index.html')


@app.route('/picme.jpeg')
def serve_logo():
    """Serve the PicMe logo image"""
    frontend_dir = os.path.join(BASE_DIR, '..', 'frontend')
    # Try JPEG first, fallback to SVG
    if os.path.exists(os.path.join(frontend_dir, 'picme.jpeg')):
        return send_from_directory(frontend_dir, 'picme.jpeg')
    else:
        return send_from_directory(frontend_dir, 'picme.svg')

@app.route('/picme.svg')
def serve_logo_svg():
    """Serve the PicMe logo SVG"""
    frontend_dir = os.path.join(BASE_DIR, '..', 'frontend')
    return send_from_directory(frontend_dir, 'picme.svg')


@app.route('/login')
def serve_login_page():
    return render_template('login.html')


@app.route('/signup')
def serve_signup_page():
    return render_template('signup.html')


@app.route('/homepage')
@login_required
def serve_homepage():
    import time
    return render_template('homepage.html', cache_bust=int(time.time()))


@app.route('/event_discovery')
@login_required
def serve_event_discovery():
    return render_template('event_discovery.html')


@app.route('/event_detail')
@login_required
def serve_event_detail():
    return render_template('event_detail.html')


@app.route('/biometric_authentication_portal')
@login_required
def serve_biometric_authentication_portal():
    return render_template('biometric_authentication_portal.html')


@app.route('/personal_photo_gallery')
@login_required
def serve_personal_photo_gallery():
    return render_template('personal_photo_gallery.html')


@app.route('/download_page')
@login_required
def serve_download_page():
    return render_template('download_page.html')


@app.route('/event_organizer')
def serve_event_organizer():
    # Allow access for admins or logged-in users (organizers)
    if not session.get('admin_logged_in') and not session.get('logged_in'):
        return redirect(url_for('serve_index'))
    return render_template('event_organizer.html')


# --- AUTH API ROUTES ---
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    full_name = data.get('fullName')
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('userType', 'user')

    if not all([full_name, email, password]):
        return jsonify({"success": False, "error": "All fields are required"}), 400

    from werkzeug.security import generate_password_hash
    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Check for existing email
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"success": False, "error": "Email already registered"}), 409

        cursor.execute(
            """
            INSERT INTO users (full_name, email, password, user_type)
            VALUES (%s, %s, %s, %s)
            """,
            (full_name, email, hashed_password, user_type)
        )
        conn.commit()
        return jsonify({"success": True, "message": "Registration successful!"}), 201

    except Exception as err:
        print(f"Registration error: {err}")
        conn.rollback()
        return jsonify({"success": False, "error": "Registration failed"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"success": False, "error": "Email and password are required"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500

    from werkzeug.security import check_password_hash

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            "SELECT id, email, password, user_type FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_type'] = user.get('user_type', 'user')

            redirect_url = '/event_organizer' if session['user_type'] == 'organizer' else '/homepage'
            return jsonify({
                "success": True,
                "message": "Login successful!",
                "redirect": redirect_url
            }), 200
        else:
            return jsonify({"success": False, "error": "Invalid email or password"}), 401

    except Exception as err:
        print(f"Error during login: {err}")
        return jsonify({
            "success": False,
            "error": "An internal server error occurred during login."
        }), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/logout')
def logout_user():
    session.clear()
    return redirect(url_for('serve_index'))


# --- ADMIN AUTH ROUTES ---
@app.route('/admin/register', methods=['POST'])
def admin_register():
    data = request.get_json()
    organization_name = data.get('organizationName')
    email = data.get('email')
    password = data.get('password')

    if not organization_name or not email or not password:
        return jsonify({"success": False, "error": "All fields are required"}), 400

    from werkzeug.security import generate_password_hash
    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()

        # Check if admin email already exists
        cursor.execute("SELECT id FROM admins WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Admin email already registered"}), 400

        # Insert new admin into admins table
        cursor.execute(
            """
            INSERT INTO admins (organization_name, email, password)
            VALUES (%s, %s, %s)
            """,
            (organization_name, email, hashed_password)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Admin account created successfully"})

    except Exception as e:
        print(f"Error during admin registration: {e}")
        if conn:
            conn.close()
        return jsonify({"success": False, "error": "Registration failed"}), 500


@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    from werkzeug.security import check_password_hash

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin and check_password_hash(admin['password'], password):
            # Create admin session
            session['admin_logged_in'] = True
            session['admin_id'] = admin['id']
            session['admin_email'] = admin['email']
            session['admin_organization'] = admin['organization_name']

            return jsonify({
                "success": True,
                "message": "Admin login successful",
                "redirect": "/event_organizer"
            })
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401

    except Exception as e:
        print(f"Error during admin login: {e}")
        if conn:
            conn.close()
        return jsonify({"success": False, "message": "Login failed"}), 500


@app.route('/admin/logout')
def admin_logout():
    # Clear only admin session keys, preserve user session if exists
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    session.pop('admin_email', None)
    session.pop('admin_organization', None)
    return redirect(url_for('serve_index'))


# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('serve_index'))
        return f(*args, **kwargs)
    return decorated_function


# --- EVENTS API / PUBLIC DATA ---
@app.route('/events', methods=['GET'])
def get_events():
    try:
        if os.path.exists(EVENTS_DATA_PATH):
            with open(EVENTS_DATA_PATH, 'r') as f:
                events_data = json.load(f)
        else:
            events_data = []
        return jsonify(events_data)
    except Exception as e:
        print(f"Error loading events: {e}")
        return jsonify([])


# --- FACE RECOGNITION ---
@app.route('/recognize', methods=['POST'])
@login_required
def recognize_face():
    """
    Recognize face from either:
      - legacy: { "image": "<base64>" }
      - new:    { "images": ["<b64_1>", "<b64_2>", ...], "challenge_type": "BLINK"|"HEAD_TURN"|None }

    Multi-frame path aggregates multiple frames using quality scores,
    and applies liveness + anti-spoof checks before identification.
    """
    try:
        data = request.get_json() or {}
        event_id = data.get('event_id', 'default_event')

        frames_b64 = data.get('images')  # NEW: list of frames
        single_b64 = data.get('image')   # OLD: single frame
        challenge_type = data.get('challenge_type')

        if not frames_b64 and not single_b64:
            return jsonify({"success": False, "error": "No image provided"}), 400

        # --- Multi-frame path (preferred) ---
        if isinstance(frames_b64, list) and len(frames_b64) > 0:
            frames_bgr = []
            for b64_str in frames_b64:
                try:
                    img_bytes = base64.b64decode(b64_str)
                    np_arr = np.frombuffer(img_bytes, np.uint8)
                    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        frames_bgr.append(frame)
                except Exception as e:
                    print(f"[RECOGNIZE] Failed to decode one frame: {e}")

            if not frames_bgr:
                return jsonify({
                    "success": False,
                    "error": "Could not decode any webcam frames."
                }), 400

            # --- LIVENESS / SPOOF CHECK BEFORE MATCHING ---
            is_live, debug_info = verify_liveness_from_bgr_frames(frames_bgr, challenge_type)
            print(f"[LIVENESS DEBUG] {debug_info}")
            if not is_live:
                return jsonify({
                    "success": False,
                    "error": "Liveness check failed. Please follow the on-screen challenge with your real face (no photos or screens)."
                }), 403

            # If live → build robust encoding
            scanned_encoding = aggregate_face_encoding_from_bgr_frames(frames_bgr)
            if scanned_encoding is None:
                return jsonify({
                    "success": False,
                    "error": "No clear face detected in captured frames."
                }), 400

        # --- Legacy single-frame path (still supported, no liveness) ---
        else:
            img_bytes = base64.b64decode(single_b64)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is None:
                return jsonify({
                    "success": False,
                    "error": "Unable to decode image."
                }), 400

            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_img)
            if not face_locations:
                return jsonify({
                    "success": False,
                    "error": "No face detected in scan."
                }), 400

            scanned_encoding = face_recognition.face_encodings(
                rgb_img, face_locations
            )[0]

        # --- Use ML model for identification ---
        person_id = model.recognize_face(scanned_encoding)

        if not person_id:
            return jsonify({
                "success": False,
                "error": "No confident match found."
            }), 404

        # Reinforce identity with this new high-quality encoding
        try:
            idx = model.known_ids.index(person_id)
            model.update_person_encoding(idx, scanned_encoding)
        except ValueError:
            # If for some reason ID isn't in list, just ignore
            pass

        # Store person_id in session for future API calls
        session['person_id'] = person_id

        # Locate this person's photos for the requested event
        person_dir = os.path.join(app.config['PROCESSED_FOLDER'], event_id, person_id)
        if not os.path.exists(person_dir):
            return jsonify({
                "success": False,
                "error": "Match found, but no photos in this event."
            }), 404

        individual_dir = os.path.join(person_dir, "individual")
        group_dir = os.path.join(person_dir, "group")

        individual_photos = (
            [f for f in os.listdir(individual_dir)]
            if os.path.exists(individual_dir) else []
        )
        group_photos = (
            [f for f in os.listdir(group_dir) if f.startswith('watermarked_')]
            if os.path.exists(group_dir) else []
        )

        return jsonify({
            "success": True,
            "person_id": person_id,
            "individual_photos": individual_photos,
            "group_photos": group_photos,
            "event_id": event_id
        })

    except Exception as e:
        print(f"[RECOGNIZE ERROR]: {e}")
        return jsonify({
            "success": False,
            "error": "An internal error occurred."
        }), 500


# --- EVENT ORGANIZER API ---
@app.route('/api/create_event', methods=['POST'])
def create_event():
    # Allow access for admins or logged-in users
    if not session.get('admin_logged_in') and not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    try:
        # Check if request has multipart form data (with thumbnail) or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Multipart form data with optional thumbnail
            event_name = request.form.get('eventName')
            event_location = request.form.get('eventLocation')
            event_date = request.form.get('eventDate')
            event_category = request.form.get('eventCategory', 'General')
            thumbnail_file = request.files.get('thumbnail')
        else:
            # JSON data (legacy support)
            data = request.get_json()
            event_name = data.get('eventName')
            event_location = data.get('eventLocation')
            event_date = data.get('eventDate')
            event_category = data.get('eventCategory', 'General')
            thumbnail_file = None

        if not all([event_name, event_location, event_date]):
            return jsonify({"success": False, "error": "All fields are required"}), 400

        event_id = f"event_{uuid.uuid4().hex[:8]}"

        # Folder structure
        event_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], event_id)
        event_processed_dir = os.path.join(app.config['PROCESSED_FOLDER'], event_id)
        os.makedirs(event_upload_dir, exist_ok=True)
        os.makedirs(event_processed_dir, exist_ok=True)

        # Handle thumbnail upload
        thumbnail_filename = None
        thumbnail_path = "/static/images/default_event.jpg"
        
        if thumbnail_file and thumbnail_file.filename:
            # Validate file format
            allowed_extensions = {'.png', '.jpg', '.jpeg'}
            file_ext = os.path.splitext(thumbnail_file.filename)[1].lower()
            
            if file_ext not in allowed_extensions:
                return jsonify({
                    "success": False, 
                    "error": f"Invalid image format. Allowed formats: PNG, JPG, JPEG"
                }), 400
            
            # Generate unique filename with thumbnail_ prefix
            thumbnail_filename = f"thumbnail_{uuid.uuid4().hex[:8]}{file_ext}"
            thumbnail_file_path = os.path.join(event_upload_dir, thumbnail_filename)
            
            # Save thumbnail file
            thumbnail_file.save(thumbnail_file_path)
            
            # Update thumbnail path to use API endpoint
            thumbnail_path = f"/api/events/{event_id}/thumbnail"

        # QR code
        qr_data = f"{request.host_url.rstrip('/')}/event_detail?event_id={event_id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join(event_upload_dir, f"{event_id}_qr.png")
        qr_img.save(qr_path)

        # events_data.json
        if os.path.exists(EVENTS_DATA_PATH):
            with open(EVENTS_DATA_PATH, 'r') as f:
                events_data = json.load(f)
        else:
            events_data = []

        # Determine who created the event (admin or regular user)
        created_by_admin_id = session.get('admin_id') if session.get('admin_logged_in') else None
        created_by_user_id = session.get('user_id') if not session.get('admin_logged_in') else None
        
        new_event = {
            "id": event_id,
            "name": event_name,
            "location": event_location,
            "date": event_date,
            "category": event_category,
            "image": thumbnail_path,
            "thumbnail_filename": thumbnail_filename,
            "photos_count": 0,
            "qr_code": f"/api/qr_code/{event_id}",
            "created_by_admin_id": created_by_admin_id,
            "created_by_user_id": created_by_user_id,
            "created_at": datetime.now().isoformat(),
            "sample_photos": []
        }

        events_data.append(new_event)
        with open(EVENTS_DATA_PATH, 'w') as f:
            json.dump(events_data, f, indent=2)

        return jsonify({
            "success": True,
            "event_id": event_id,
            "message": "Event created successfully!"
        }), 201

    except Exception as e:
        print(f"Error creating event: {e}")
        return jsonify({"success": False, "error": "Failed to create event"}), 500


@app.route('/api/qr_code/<event_id>')
def get_qr_code(event_id):
    qr_path = os.path.join(app.config['UPLOAD_FOLDER'], event_id, f"{event_id}_qr.png")
    if os.path.exists(qr_path):
        return send_from_directory(
            os.path.join(app.config['UPLOAD_FOLDER'], event_id),
            f"{event_id}_qr.png"
        )
    return "QR Code not found", 404


@app.route('/api/events/<event_id>/thumbnail')
def get_event_thumbnail(event_id):
    """Serve event thumbnail"""
    # Load events data to get thumbnail filename
    if os.path.exists(EVENTS_DATA_PATH):
        with open(EVENTS_DATA_PATH, 'r') as f:
            events_data = json.load(f)
        
        # Find the event
        event = next((e for e in events_data if e['id'] == event_id), None)
        if event and event.get('thumbnail_filename'):
            thumbnail_path = os.path.join(
                app.config['UPLOAD_FOLDER'], 
                event_id, 
                event['thumbnail_filename']
            )
            if os.path.exists(thumbnail_path):
                return send_from_directory(
                    os.path.join(app.config['UPLOAD_FOLDER'], event_id),
                    event['thumbnail_filename']
                )
    
    return "Thumbnail not found", 404


@app.route('/api/upload_photos/<event_id>', methods=['POST'])
def upload_event_photos(event_id):
    # Allow access for admins or logged-in users
    if not session.get('admin_logged_in') and not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    try:
        if 'photos' not in request.files:
            return jsonify({"success": False, "error": "No photos uploaded"}), 400

        files = request.files.getlist('photos')
        if not files or files[0].filename == '':
            return jsonify({"success": False, "error": "No photos selected"}), 400

        event_dir = os.path.join(app.config['UPLOAD_FOLDER'], event_id)
        if not os.path.exists(event_dir):
            return jsonify({"success": False, "error": "Event not found"}), 404

        uploaded_files = []
        for file in files:
            if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
                file_path = os.path.join(event_dir, filename)
                file.save(file_path)
                uploaded_files.append(filename)

        # Process in background
        threading.Thread(target=process_images, args=(event_id,)).start()

        # Update photo count
        if os.path.exists(EVENTS_DATA_PATH):
            with open(EVENTS_DATA_PATH, 'r') as f:
                events_data = json.load(f)

            for event in events_data:
                if event['id'] == event_id:
                    event['photos_count'] += len(uploaded_files)
                    break

            with open(EVENTS_DATA_PATH, 'w') as f:
                json.dump(events_data, f, indent=2)

        return jsonify({
            "success": True,
            "message": f"Successfully uploaded {len(uploaded_files)} photos",
            "uploaded_files": uploaded_files
        }), 200

    except Exception as e:
        print(f"Error uploading photos: {e}")
        return jsonify({"success": False, "error": "Failed to upload photos"}), 500


@app.route('/api/my_events')
def get_my_events():
    # Allow access for admins or logged-in users
    if not session.get('admin_logged_in') and not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    try:
        if os.path.exists(EVENTS_DATA_PATH):
            with open(EVENTS_DATA_PATH, 'r') as f:
                all_events = json.load(f)

            # Filter events based on who is logged in
            if session.get('admin_logged_in'):
                # Admin sees only their events
                admin_id = session.get('admin_id')
                user_events = [
                    event for event in all_events
                    if event.get('created_by_admin_id') == admin_id
                ]
            else:
                # Regular user sees only their events
                user_id = session.get('user_id')
                user_events = [
                    event for event in all_events
                    if event.get('created_by_user_id') == user_id
                ]
            
            return jsonify({"success": True, "events": user_events})

        return jsonify({"success": True, "events": []})

    except Exception as e:
        print(f"Error fetching events: {e}")
        return jsonify({"success": False, "error": "Failed to fetch events"}), 500


@app.route('/api/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    """
    Update event details (name, location, date, category)
    Requires admin authentication and ownership validation
    """
    # Check admin authentication
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Validate required fields
        name = data.get('name')
        location = data.get('location')
        date = data.get('date')
        category = data.get('category')
        
        if not all([name, location, date, category]):
            return jsonify({
                "success": False, 
                "error": "All fields are required (name, location, date, category)"
            }), 400
        
        # Load events data
        if not os.path.exists(EVENTS_DATA_PATH):
            return jsonify({"success": False, "error": "Events data file not found"}), 404
        
        with open(EVENTS_DATA_PATH, 'r') as f:
            events_data = json.load(f)
        
        # Find the event
        event = None
        event_index = None
        for i, e in enumerate(events_data):
            if e['id'] == event_id:
                event = e
                event_index = i
                break
        
        if not event:
            return jsonify({"success": False, "error": "Event not found"}), 404
        
        # Check ownership - admin can only edit their own events
        admin_id = session.get('admin_id')
        if event.get('created_by_admin_id') != admin_id:
            return jsonify({
                "success": False, 
                "error": "You can only edit events you created"
            }), 403
        
        # Update event fields
        event['name'] = name
        event['location'] = location
        event['date'] = date
        event['category'] = category
        
        # Save updated events data
        with open(EVENTS_DATA_PATH, 'w') as f:
            json.dump(events_data, f, indent=2)
        
        return jsonify({
            "success": True,
            "event": event,
            "message": "Event updated successfully"
        }), 200
    
    except Exception as e:
        print(f"Error updating event: {e}")
        return jsonify({
            "success": False, 
            "error": "Failed to update event"
        }), 500


@app.route('/api/events/<event_id>/thumbnail', methods=['POST'])
def update_event_thumbnail(event_id):
    """
    Upload or update event thumbnail
    Requires admin authentication and ownership validation
    """
    # Check admin authentication
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        # Check if thumbnail file is provided
        if 'thumbnail' not in request.files:
            return jsonify({"success": False, "error": "No thumbnail file provided"}), 400
        
        thumbnail_file = request.files['thumbnail']
        
        if not thumbnail_file or thumbnail_file.filename == '':
            return jsonify({"success": False, "error": "No thumbnail file selected"}), 400
        
        # Validate file format
        allowed_extensions = {'.png', '.jpg', '.jpeg'}
        file_ext = os.path.splitext(thumbnail_file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({
                "success": False, 
                "error": "Invalid image format. Allowed formats: PNG, JPG, JPEG"
            }), 400
        
        # Load events data
        if not os.path.exists(EVENTS_DATA_PATH):
            return jsonify({"success": False, "error": "Events data file not found"}), 404
        
        with open(EVENTS_DATA_PATH, 'r') as f:
            events_data = json.load(f)
        
        # Find the event
        event = None
        event_index = None
        for i, e in enumerate(events_data):
            if e['id'] == event_id:
                event = e
                event_index = i
                break
        
        if not event:
            return jsonify({"success": False, "error": "Event not found"}), 404
        
        # Check ownership - admin can only edit their own events
        admin_id = session.get('admin_id')
        if event.get('created_by_admin_id') != admin_id:
            return jsonify({
                "success": False, 
                "error": "You can only edit events you created"
            }), 403
        
        # Get event upload directory
        event_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], event_id)
        if not os.path.exists(event_upload_dir):
            os.makedirs(event_upload_dir, exist_ok=True)
        
        # Delete old thumbnail file if it exists
        old_thumbnail_filename = event.get('thumbnail_filename')
        if old_thumbnail_filename:
            old_thumbnail_path = os.path.join(event_upload_dir, old_thumbnail_filename)
            if os.path.exists(old_thumbnail_path):
                try:
                    os.remove(old_thumbnail_path)
                    print(f"Deleted old thumbnail: {old_thumbnail_path}")
                except Exception as e:
                    print(f"Warning: Failed to delete old thumbnail: {e}")
        
        # Generate unique filename with thumbnail_ prefix
        new_thumbnail_filename = f"thumbnail_{uuid.uuid4().hex[:8]}{file_ext}"
        new_thumbnail_path = os.path.join(event_upload_dir, new_thumbnail_filename)
        
        # Save new thumbnail file
        thumbnail_file.save(new_thumbnail_path)
        
        # Update event data with new thumbnail
        event['thumbnail_filename'] = new_thumbnail_filename
        event['image'] = f"/api/events/{event_id}/thumbnail"
        
        # Save updated events data
        with open(EVENTS_DATA_PATH, 'w') as f:
            json.dump(events_data, f, indent=2)
        
        return jsonify({
            "success": True,
            "thumbnail_url": event['image'],
            "message": "Thumbnail updated successfully"
        }), 200
    
    except Exception as e:
        print(f"Error updating thumbnail: {e}")
        return jsonify({
            "success": False, 
            "error": "Failed to update thumbnail"
        }), 500


@app.route('/api/delete_event/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    """
    Delete an event and all associated data (photos, folders, metadata)
    Requires admin authentication and ownership validation
    """
    # Check admin authentication
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        # Load events data
        if not os.path.exists(EVENTS_DATA_PATH):
            return jsonify({"success": False, "error": "Events data file not found"}), 404
        
        with open(EVENTS_DATA_PATH, 'r') as f:
            events_data = json.load(f)
        
        # Find the event
        event = None
        event_index = None
        for i, e in enumerate(events_data):
            if e['id'] == event_id:
                event = e
                event_index = i
                break
        
        if not event:
            return jsonify({"success": False, "error": "Event not found"}), 404
        
        # Check ownership - admin can only delete their own events
        admin_id = session.get('admin_id')
        if event.get('created_by_admin_id') != admin_id:
            return jsonify({
                "success": False, 
                "error": "You can only delete events you created"
            }), 403
        
        # Delete event folders (uploads and processed)
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], event_id)
        processed_dir = os.path.join(app.config['PROCESSED_FOLDER'], event_id)
        
        # Delete upload folder
        if os.path.exists(upload_dir):
            try:
                shutil.rmtree(upload_dir)
                print(f"Deleted upload folder: {upload_dir}")
            except Exception as e:
                print(f"Warning: Failed to delete upload folder: {e}")
        
        # Delete processed folder
        if os.path.exists(processed_dir):
            try:
                shutil.rmtree(processed_dir)
                print(f"Deleted processed folder: {processed_dir}")
            except Exception as e:
                print(f"Warning: Failed to delete processed folder: {e}")
        
        # Remove event from events_data.json
        events_data.pop(event_index)
        
        # Save updated events data
        with open(EVENTS_DATA_PATH, 'w') as f:
            json.dump(events_data, f, indent=2)
        
        return jsonify({
            "success": True,
            "message": "Event deleted successfully"
        }), 200
    
    except Exception as e:
        print(f"Error deleting event: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "error": "Failed to delete event"
        }), 500


# --- PUBLIC & PRIVATE PHOTO SERVING ---
@app.route('/api/events/<event_id>/photos', methods=['GET'])
def get_event_photos(event_id):
    # (simple version: no pagination, returns all group photos)
    event_dir = os.path.join(app.config['PROCESSED_FOLDER'], event_id)
    if not os.path.exists(event_dir):
        return jsonify({"success": False, "error": "No photos found for this event yet."}), 404

    unique_photos = set()
    for person_id in os.listdir(event_dir):
        group_dir = os.path.join(event_dir, person_id, "group")
        if os.path.exists(group_dir):
            for filename in os.listdir(group_dir):
                if filename.startswith('watermarked_'):
                    unique_photos.add(filename)

    photo_urls = [
        f"/photos/{event_id}/all/{filename}"
        for filename in sorted(list(unique_photos))
    ]
    # Frontend expects success + photos; you can add has_next if you later add pagination
    return jsonify({"success": True, "photos": photo_urls, "has_next": False})


@app.route('/photos/<event_id>/all/<filename>')
def get_public_photo(event_id, filename):
    event_dir = os.path.join(app.config['PROCESSED_FOLDER'], event_id)
    for person_id in os.listdir(event_dir):
        photo_path = os.path.join(event_dir, person_id, "group", filename)
        if os.path.exists(photo_path):
            return send_from_directory(
                os.path.join(event_dir, person_id, "group"),
                filename
            )
    return "File Not Found", 404


@app.route('/photos/<event_id>/<person_id>/<photo_type>/<filename>')
def get_private_photo(event_id, person_id, photo_type, filename):
    # Allow access for admins or logged-in users
    if not session.get('admin_logged_in') and not session.get('logged_in'):
        return "Unauthorized", 401

    photo_path = os.path.join(
        app.config['PROCESSED_FOLDER'],
        event_id,
        person_id,
        photo_type
    )
    return send_from_directory(photo_path, filename)


@app.route('/api/user_photos', methods=['GET'])
@login_required
def get_user_photos():
    """
    Get all photos for the authenticated user across all events.
    Returns events with photo metadata organized by event.
    """
    try:
        # Validate session is still active
        if not session.get('user_email'):
            return jsonify({
                "success": False,
                "error": "Session expired. Please log in again.",
                "error_code": "SESSION_EXPIRED"
            }), 401
        
        # Get person_id from session (set during face recognition)
        person_id = session.get('person_id')
        
        if not person_id:
            return jsonify({
                "success": False,
                "error": "No person_id found. Please authenticate via biometric scan first.",
                "error_code": "NO_PERSON_ID"
            }), 404

        # Load events metadata with error handling
        events_data = []
        try:
            if os.path.exists(EVENTS_DATA_PATH):
                with open(EVENTS_DATA_PATH, 'r') as f:
                    events_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading events data: {e}")
            # Continue with empty events_data - we'll use defaults

        # Scan processed folder for user's photos across all events
        user_events = []
        total_photos = 0

        if not os.path.exists(app.config['PROCESSED_FOLDER']):
            print(f"Processed folder does not exist: {app.config['PROCESSED_FOLDER']}")
            return jsonify({
                "success": True,
                "events": [],
                "total_photos": 0
            })

        try:
            for event_id in os.listdir(app.config['PROCESSED_FOLDER']):
                event_dir = os.path.join(app.config['PROCESSED_FOLDER'], event_id)
                
                if not os.path.isdir(event_dir):
                    continue

                # Check if this person has photos in this event
                person_dir = os.path.join(event_dir, person_id)
                
                if not os.path.exists(person_dir):
                    continue

                # Get individual and group photos
                individual_dir = os.path.join(person_dir, "individual")
                group_dir = os.path.join(person_dir, "group")

                individual_photos = []
                group_photos = []

                try:
                    if os.path.exists(individual_dir):
                        for filename in os.listdir(individual_dir):
                            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                                individual_photos.append({
                                    "filename": filename,
                                    "url": f"/photos/{event_id}/{person_id}/individual/{filename}"
                                })
                except OSError as e:
                    print(f"Error reading individual photos for {event_id}: {e}")
                    # Continue with empty list

                try:
                    if os.path.exists(group_dir):
                        for filename in os.listdir(group_dir):
                            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                                group_photos.append({
                                    "filename": filename,
                                    "url": f"/photos/{event_id}/{person_id}/group/{filename}"
                                })
                except OSError as e:
                    print(f"Error reading group photos for {event_id}: {e}")
                    # Continue with empty list

                # Only include events where user has photos
                if individual_photos or group_photos:
                    # Find event metadata
                    event_metadata = next(
                        (e for e in events_data if e['id'] == event_id),
                        {
                            "name": event_id,
                            "location": "Unknown",
                            "date": "Unknown",
                            "category": "General"
                        }
                    )

                    event_info = {
                        "event_id": event_id,
                        "event_name": event_metadata.get('name', event_id),
                        "event_date": event_metadata.get('date', 'Unknown'),
                        "event_location": event_metadata.get('location', 'Unknown'),
                        "event_category": event_metadata.get('category', 'General'),
                        "person_id": person_id,
                        "individual_photos": individual_photos,
                        "group_photos": group_photos,
                        "photo_count": len(individual_photos) + len(group_photos)
                    }

                    user_events.append(event_info)
                    total_photos += event_info['photo_count']
        except OSError as e:
            print(f"Error scanning processed folder: {e}")
            return jsonify({
                "success": False,
                "error": "Unable to access photo storage. Please try again later.",
                "error_code": "STORAGE_ERROR"
            }), 500

        # Sort events by date (most recent first)
        user_events.sort(key=lambda x: x['event_date'], reverse=True)

        return jsonify({
            "success": True,
            "events": user_events,
            "total_photos": total_photos
        })

    except Exception as e:
        print(f"Error fetching user photos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred while loading your photos. Please try again.",
            "error_code": "INTERNAL_ERROR"
        }), 500


@app.route('/api/download_photos', methods=['POST'])
@login_required
def download_photos():
    """
    Download multiple photos as a ZIP file (for personal gallery)
    """
    zip_path = None
    try:
        import zipfile
        from flask import send_file
        
        # Validate session is still active
        if not session.get('user_email'):
            return jsonify({
                "success": False,
                "error": "Session expired. Please log in again.",
                "error_code": "SESSION_EXPIRED"
            }), 401
        
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False, 
                "error": "Invalid request format",
                "error_code": "INVALID_REQUEST"
            }), 400
            
        event_id = data.get('event_id')
        person_id = data.get('person_id')
        photos = data.get('photos', [])

        if not all([event_id, person_id, photos]):
            return jsonify({
                "success": False, 
                "error": "Missing required parameters (event_id, person_id, or photos)",
                "error_code": "MISSING_PARAMETERS"
            }), 400
        
        # Validate photos is a list
        if not isinstance(photos, list):
            return jsonify({
                "success": False,
                "error": "Invalid photos parameter. Expected a list.",
                "error_code": "INVALID_PHOTOS_FORMAT"
            }), 400
        
        # Validate photos list is not empty
        if len(photos) == 0:
            return jsonify({
                "success": False,
                "error": "No photos selected for download.",
                "error_code": "NO_PHOTOS_SELECTED"
            }), 400

        # Validate photo count and estimate size (max 100MB)
        MAX_PHOTOS = 500
        if len(photos) > MAX_PHOTOS:
            return jsonify({
                "success": False,
                "error": f"Too many photos selected. Maximum is {MAX_PHOTOS} photos per download.",
                "error_code": "TOO_MANY_PHOTOS"
            }), 413

        # Check disk space availability
        try:
            import shutil
            stat = shutil.disk_usage(app.config['PROCESSED_FOLDER'])
            free_space = stat.free
            MIN_FREE_SPACE = 200 * 1024 * 1024  # Require at least 200MB free
            
            if free_space < MIN_FREE_SPACE:
                return jsonify({
                    "success": False,
                    "error": "Insufficient disk space on server. Please try again later.",
                    "error_code": "INSUFFICIENT_DISK_SPACE"
                }), 507
        except Exception as e:
            print(f"Warning: Could not check disk space: {e}")
            # Continue anyway - this is just a precaution
        
        # Create a temporary ZIP file
        zip_filename = f"photos_{event_id}_{person_id}_{uuid.uuid4().hex[:8]}.zip"
        zip_path = os.path.join(app.config['PROCESSED_FOLDER'], zip_filename)

        photos_added = 0
        total_size = 0
        MAX_ZIP_SIZE = 100 * 1024 * 1024  # 100MB

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for photo in photos:
                    # Validate photo object structure
                    if not isinstance(photo, dict):
                        print(f"Invalid photo object: {photo}")
                        continue
                    
                    filename = photo.get('filename')
                    photo_type = photo.get('photoType')
                    
                    if not filename or not photo_type:
                        print(f"Missing filename or photoType: {photo}")
                        continue
                    
                    # Validate photo_type
                    if photo_type not in ['individual', 'group']:
                        print(f"Invalid photo_type: {photo_type}")
                        continue
                    
                    # Remove watermarked_ prefix if present for the actual file
                    actual_filename = filename.replace('watermarked_', '') if filename.startswith('watermarked_') else filename
                    
                    # Sanitize filename to prevent path traversal
                    actual_filename = os.path.basename(actual_filename)
                    
                    photo_path = os.path.join(
                        app.config['PROCESSED_FOLDER'],
                        event_id,
                        person_id,
                        photo_type,
                        filename
                    )

                    if os.path.exists(photo_path):
                        try:
                            # Check file size before adding
                            file_size = os.path.getsize(photo_path)
                            if total_size + file_size > MAX_ZIP_SIZE:
                                print(f"ZIP size limit reached: {total_size} bytes")
                                # Return partial success with warning
                                if photos_added > 0:
                                    break
                                else:
                                    if zip_path and os.path.exists(zip_path):
                                        os.remove(zip_path)
                                    return jsonify({
                                        "success": False,
                                        "error": "Selected photos exceed size limit (100MB). Please select fewer photos.",
                                        "error_code": "ZIP_SIZE_LIMIT"
                                    }), 413
                            
                            # Verify file is readable
                            with open(photo_path, 'rb') as test_file:
                                test_file.read(1)
                            
                            # Add to ZIP with a clean filename
                            zipf.write(photo_path, arcname=actual_filename)
                            photos_added += 1
                            total_size += file_size
                        except (IOError, OSError) as e:
                            print(f"Error reading photo {photo_path}: {e}")
                            continue
                    else:
                        print(f"Photo not found: {photo_path}")
        except zipfile.BadZipFile as e:
            print(f"Bad ZIP file error: {e}")
            if zip_path and os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except:
                    pass
            return jsonify({
                "success": False,
                "error": "Unable to create valid ZIP file. Please try again.",
                "error_code": "BAD_ZIP_FILE"
            }), 500
        except OSError as e:
            print(f"Error creating ZIP file: {e}")
            if zip_path and os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except:
                    pass
            
            # Check if it's a disk space issue
            if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                return jsonify({
                    "success": False,
                    "error": "Server disk space full. Please try again later or select fewer photos.",
                    "error_code": "DISK_FULL"
                }), 507
            
            return jsonify({
                "success": False,
                "error": "Unable to create download file. Please try again.",
                "error_code": "ZIP_CREATION_ERROR"
            }), 500
        except MemoryError as e:
            print(f"Memory error creating ZIP: {e}")
            if zip_path and os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except:
                    pass
            return jsonify({
                "success": False,
                "error": "Too many photos selected. Please select fewer photos.",
                "error_code": "MEMORY_ERROR"
            }), 413

        if photos_added == 0:
            # Clean up empty ZIP
            if os.path.exists(zip_path):
                os.remove(zip_path)
            return jsonify({
                "success": False,
                "error": "No photos were found to download. They may have been deleted.",
                "error_code": "NO_PHOTOS_FOUND"
            }), 404

        # Verify ZIP file exists and has content
        if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
            return jsonify({
                "success": False,
                "error": "Failed to create download file",
                "error_code": "EMPTY_ZIP"
            }), 500

        # Send the ZIP file
        try:
            response = send_file(
                zip_path,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f"picme_photos_{event_id}.zip"
            )
        except Exception as e:
            print(f"Error sending ZIP file: {e}")
            if zip_path and os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except:
                    pass
            return jsonify({
                "success": False,
                "error": "Failed to send download file",
                "error_code": "SEND_ERROR"
            }), 500

        # Schedule cleanup of the ZIP file after sending
        def cleanup_zip():
            import time
            time.sleep(5)  # Wait 5 seconds before cleanup
            try:
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                    print(f"Cleaned up temporary ZIP: {zip_path}")
            except Exception as e:
                print(f"Error cleaning up ZIP: {e}")

        threading.Thread(target=cleanup_zip).start()

        return response

    except Exception as e:
        print(f"Error creating ZIP download: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up ZIP file on error
        if zip_path and os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except:
                pass
                
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred during download. Please try again.",
            "error_code": "INTERNAL_ERROR"
        }), 500


@app.route('/api/download_event_photos', methods=['POST'])
@login_required
def download_event_photos():
    """
    Download multiple event photos as a ZIP file (for event detail page)
    """
    try:
        import zipfile
        from flask import send_file
        
        data = request.get_json()
        event_id = data.get('event_id')
        photo_urls = data.get('photo_urls', [])

        if not all([event_id, photo_urls]):
            return jsonify({"success": False, "error": "Missing required parameters"}), 400

        # Create a temporary ZIP file
        zip_filename = f"event_photos_{event_id}_{uuid.uuid4().hex[:8]}.zip"
        zip_path = os.path.join(app.config['PROCESSED_FOLDER'], zip_filename)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for photo_url in photo_urls:
                # Parse the URL to get the file path
                # URL format: /photos/event_id/all/filename
                parts = photo_url.split('/')
                if len(parts) >= 4:
                    filename = parts[-1]
                    # Remove watermarked_ prefix for cleaner filenames
                    clean_filename = filename.replace('watermarked_', '')
                    
                    # Find the actual file in the processed folder
                    event_dir = os.path.join(app.config['PROCESSED_FOLDER'], event_id)
                    if os.path.exists(event_dir):
                        for person_id in os.listdir(event_dir):
                            group_dir = os.path.join(event_dir, person_id, "group")
                            photo_path = os.path.join(group_dir, filename)
                            if os.path.exists(photo_path):
                                # Add to ZIP with clean filename
                                zipf.write(photo_path, arcname=clean_filename)
                                break

        # Send the ZIP file
        response = send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"event_photos_{event_id}.zip"
        )

        # Schedule cleanup of the ZIP file after sending
        def cleanup_zip():
            import time
            time.sleep(5)  # Wait 5 seconds before cleanup
            try:
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                    print(f"Cleaned up temporary ZIP: {zip_path}")
            except Exception as e:
                print(f"Error cleaning up ZIP: {e}")

        threading.Thread(target=cleanup_zip).start()

        return response

    except Exception as e:
        print(f"Error creating event photos ZIP download: {e}")
        return jsonify({"success": False, "error": "Failed to create download"}), 500


# --- ADMIN PHOTO ACCESS ROUTES ---
@app.route('/api/admin/events/<event_id>/all-photos', methods=['GET'])
def get_admin_all_photos(event_id):
    """Admin endpoint to get ORIGINAL uploaded photos for an event (no duplicates)"""
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "error": "Admin access required"}), 403

    # Get photos from uploads folder (original photos only)
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], event_id)
    if not os.path.exists(upload_dir):
        return jsonify({"success": False, "error": "No photos found for this event yet."}), 404

    all_photos = []

    # Get all original uploaded photos
    for filename in os.listdir(upload_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')) and not filename.endswith('_qr.png'):
            all_photos.append({
                "url": f"/api/admin/photos/{event_id}/{filename}",
                "filename": filename,
                "original_filename": filename
            })

    return jsonify({
        "success": True,
        "photos": all_photos,
        "total": len(all_photos)
    })


@app.route('/api/admin/photos/<event_id>/<filename>')
def serve_admin_photo(event_id, filename):
    """Serve original uploaded photos to admin"""
    if not session.get('admin_logged_in'):
        return "Unauthorized", 403

    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], event_id)
    if os.path.exists(os.path.join(upload_dir, filename)):
        return send_from_directory(upload_dir, filename)
    return "File Not Found", 404


@app.route('/api/admin/photos/delete', methods=['POST'])
def delete_photo():
    """Admin endpoint to delete a photo from uploads folder"""
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "error": "Admin access required"}), 403

    data = request.get_json()
    event_id = data.get('event_id')
    filename = data.get('filename')

    if not all([event_id, filename]):
        return jsonify({"success": False, "error": "Missing required parameters"}), 400

    # Delete from uploads folder
    upload_path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        event_id,
        filename
    )

    try:
        # Delete the original uploaded photo
        if os.path.exists(upload_path):
            os.remove(upload_path)
            print(f"Deleted upload photo: {upload_path}")
        else:
            return jsonify({"success": False, "error": "Photo not found"}), 404

        # Update events_data.json photo count
        if os.path.exists(EVENTS_DATA_PATH):
            with open(EVENTS_DATA_PATH, 'r') as f:
                events_data = json.load(f)

            for event in events_data:
                if event['id'] == event_id and event.get('photos_count', 0) > 0:
                    event['photos_count'] -= 1
                    break

            with open(EVENTS_DATA_PATH, 'w') as f:
                json.dump(events_data, f, indent=2)

        return jsonify({
            "success": True,
            "message": "Photo deleted successfully. Run reprocessing to update face recognition."
        })

    except Exception as e:
        print(f"Error deleting photo: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to delete photo: {str(e)}"
        }), 500


# --- STARTUP TASKS ---
def process_existing_uploads_on_startup():
    print("--- [LOG] Checking for existing photos on startup... ---")
    if os.path.exists(UPLOAD_FOLDER):
        for event_id in os.listdir(UPLOAD_FOLDER):
            if os.path.isdir(os.path.join(UPLOAD_FOLDER, event_id)):
                threading.Thread(target=process_images, args=(event_id,)).start()


# --- ENTRY POINT ---
if __name__ == '__main__':
    if not os.path.exists(EVENTS_DATA_PATH):
        # You can also create an empty list file here if you want
        pass

    # Auto-generate known_faces.dat if it doesn't exist and there are photos to process
    if not os.path.exists(KNOWN_FACES_DATA_PATH):
        print("[LOG] known_faces.dat not found. Checking for photos to process...")
        has_photos = False
        if os.path.exists(UPLOAD_FOLDER):
            for event_id in os.listdir(UPLOAD_FOLDER):
                event_dir = os.path.join(UPLOAD_FOLDER, event_id)
                if os.path.isdir(event_dir):
                    photos = [f for f in os.listdir(event_dir) 
                             if f.lower().endswith(('.png', '.jpg', '.jpeg')) 
                             and not f.endswith('_qr.png')]
                    if photos:
                        has_photos = True
                        break
        
        if has_photos:
            print("[LOG] Photos found. Auto-generating face recognition model...")
            process_existing_uploads_on_startup()
            print("[LOG] Face recognition model generation started in background.")
        else:
            print("[LOG] No photos found. Face recognition model will be created when photos are uploaded.")
    else:
        print("[LOG] Face recognition model loaded successfully.")

    port = int(os.environ.get("PORT", 5000))
    # Use 127.0.0.1 for localhost only, or 0.0.0.0 for network access
    app.run(host='127.0.0.1', port=port, debug=True)
