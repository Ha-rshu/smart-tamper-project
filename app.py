from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
import hashlib
import secrets
import joblib
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="templates", static_folder="static")

app.secret_key = "12345"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "tamperdb.sqlite3")

# ------------------ LOAD AI MODEL ------------------
MODEL_PATH = os.path.join(BASE_DIR, "model", "risk_model.pkl")

ai_model = joblib.load(MODEL_PATH)


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# ------------------ AI RISK PREDICTION ------------------
def predict_risk(size_diff, changed, freq, time_gap):

    result = ai_model.predict([[
        size_diff,
        changed,
        freq,
        time_gap
    ]])

    levels = ["Low", "Medium", "High"]

    return levels[result[0]]


# ------------------ DB CONNECTION ------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            stored_name TEXT NOT NULL,
            salt TEXT NOT NULL,
            hash TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS verify_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER,
        filename TEXT,
        status TEXT,
        timestamp TEXT
    )
""")

    conn.commit()
    conn.close()


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ------------------ HASH FUNCTIONS ------------------
def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def make_fingerprint(file_hash, salt):
    return hashlib.sha256((file_hash + salt).encode()).hexdigest()


# ------------------ LOGIN ------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # prototype login
        if username == "admin" and password == "admin123":
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("❌ Invalid username or password!", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# ------------------ DASHBOARD ------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    total_files = conn.execute("SELECT COUNT(*) AS c FROM files").fetchone()["c"]

    verified_count = conn.execute(
        "SELECT COUNT(*) AS c FROM verify_logs WHERE status='Verified'"
    ).fetchone()["c"]

    tampered_count = conn.execute(
        "SELECT COUNT(*) AS c FROM verify_logs WHERE status='Tampered'"
    ).fetchone()["c"]

    recent_files = conn.execute(
        "SELECT * FROM files ORDER BY id DESC LIMIT 5"
    ).fetchall()

    recent_logs = conn.execute(
        "SELECT filename, status FROM verify_logs ORDER BY id DESC LIMIT 5"
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_files=total_files,
        verified_count=verified_count,
        tampered_count=tampered_count,
        recent_files=recent_files,
        recent_logs=recent_logs
    )


# ------------------ UPLOAD & REGISTER ------------------
@app.route("/upload", methods=["GET", "POST"])
def upload_page():
    session.pop('_flashes', None)

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        if "file" not in request.files:
            flash("❌ No file selected!", "error")
            return redirect(url_for("upload_page"))

        file = request.files["file"]

        if file.filename == "":
            flash("❌ Please choose a file!", "error")
            return redirect(url_for("upload_page"))

        original_filename = file.filename
        safe_name = secure_filename(original_filename)

        stored_name = datetime.now().strftime("%Y%m%d%H%M%S_") + safe_name
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)
        file.save(save_path)

        # SHA256 + SALT + FINGERPRINT
        file_hash = sha256_file(save_path)
        salt = secrets.token_hex(16)
        fingerprint = make_fingerprint(file_hash, salt)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO files (filename, stored_name, salt, hash, timestamp) VALUES (?, ?, ?, ?, ?)",
            (original_filename, stored_name, salt, fingerprint, timestamp),
        )
        conn.commit()
        conn.close()

        flash("✅ File uploaded & registered successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("upload.html")

# ------------------ VERIFY ------------------
@app.route("/verify", methods=["GET", "POST"])
def verify_page():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    records = conn.execute("SELECT * FROM files ORDER BY id DESC").fetchall()
    conn.close()

    if request.method == "GET":
        return render_template("verify.html", records=records)

    if request.method == "POST":
        file_id = request.form.get("file_id")

        if "file" not in request.files:
            flash("❌ No file selected!", "error")
            return redirect(url_for("verify_page"))

        file = request.files["file"]
        if file.filename == "":
            flash("❌ Please choose a file!", "error")
            return redirect(url_for("verify_page"))

        # Save TEMP file
        temp_name = "TEMP_" + secure_filename(file.filename)
        temp_path = os.path.join(app.config["UPLOAD_FOLDER"], temp_name)
        file.save(temp_path)

        current_hash = sha256_file(temp_path)

        conn = get_db_connection()
        stored = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
        conn.close()

        if os.path.exists(temp_path):
            os.remove(temp_path)

    if stored is None:
        flash("❌ Record not found!", "error")
        return redirect(url_for("verify_page"))

    salt = stored["salt"]
    stored_fingerprint = stored["hash"]
    current_fingerprint = make_fingerprint(current_hash, salt)

    # ✅ Decide status
    if current_fingerprint == stored_fingerprint:
        status = "Verified"
        color = "green"
        changed = 0
    else:
        status = "Tampered"
        color = "red"
        changed = 1
    
    # AI Features
    size_diff = abs(len(current_hash) - len(stored_fingerprint))
    freq = 1
    time_gap = 1

    # Predict Risk
    risk = predict_risk(size_diff, changed, freq, time_gap)

    # ✅ SAVE LOG ENTRY IN DATABASE
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO verify_logs (file_id, filename, status, timestamp) VALUES (?, ?, ?, ?)",
        (stored["id"], stored["filename"], status, timestamp)
    )
    conn.commit()
    conn.close()

    return render_template("result.html", status=status, color=color, risk=risk)


def get_latest_version(filename):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT MAX(version) FROM files WHERE filename=?",
        (filename,)
    )

    result = cur.fetchone()[0]
    conn.close()

    return result if result else 0

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
