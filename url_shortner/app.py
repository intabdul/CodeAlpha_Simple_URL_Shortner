from flask import Flask, request, redirect, render_template, jsonify
import sqlite3
import string
import random
import os
import socket  # 👈 For auto-detecting local IP

app = Flask(__name__)
DB_NAME = "database.db"


# AUTO-DETECT LOCAL IP

def get_local_ip():
    """Return the machine's local IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # Google DNS
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

LOCAL_IP = get_local_ip()
PORT = 8080  # 👈 Changed from 5000 to 8080
BASE_URL = f"http://{LOCAL_IP}:{PORT}/"


# DATABASE

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_code TEXT UNIQUE,
                original_url TEXT NOT NULL
            )
        """)


# HELPERS

def generate_short_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def save_url_mapping(short_code, original_url):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO urls (short_code, original_url) VALUES (?, ?)",
                     (short_code, original_url))
        conn.commit()

def get_original_url(short_code):
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute("SELECT original_url FROM urls WHERE short_code = ?", (short_code,)).fetchone()
        return row[0] if row else None

# ROUTES
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        long_url = request.form.get("long_url")
        if not long_url:
            return "❌ Please enter a valid URL.", 400

        short_code = generate_short_code()
        save_url_mapping(short_code, long_url)
        return render_template("index.html", short_url=BASE_URL + short_code)

    return render_template("index.html")

@app.route("/api/shorten", methods=["POST"])
def api_shorten():
    data = request.get_json()
    long_url = data.get("long_url")
    if not long_url:
        return jsonify({"error": "Missing URL"}), 400

    short_code = generate_short_code()
    save_url_mapping(short_code, long_url)
    return jsonify({"short_url": BASE_URL + short_code})

@app.route("/<short_code>")
def redirect_to_original(short_code):
    original_url = get_original_url(short_code)
    if original_url:
        return redirect(original_url)
    return "❌ Short URL not found.", 404

# MAIN
if __name__ == "__main__":
    if not os.path.exists(DB_NAME):
        init_db()
    print(f"✅ Server running at: {BASE_URL}")
    app.run(host="0.0.0.0", port=PORT, debug=True)
