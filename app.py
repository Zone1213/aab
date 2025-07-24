# app.py

import os
import threading
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
from user import user_bp
from admin import admin_routes
from bot import run_bot, verify_telegram_init_data, extract_telegram_user
from userdata import create_user, refresh_all_leaderboards

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'super_secret_key_here')


# ── Serve favicon to avoid 404 ──
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'icons'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


# ── Root redirects to dashboard ──
@app.route('/')
def index():
    return redirect(url_for('dashboard'))


# ── Telegram WebApp Authentication ──
@app.route('/auth')
def auth():
    init_data = request.args.get('initData')
    if not init_data or not verify_telegram_init_data(init_data):
        return "Missing or invalid Telegram initData", 400

    tg_user = extract_telegram_user(init_data)
    username = tg_user.get('username') or f"user_{tg_user.get('id')}"
    session['username'] = username
    create_user(username)
    return redirect(url_for('dashboard'))


# ── Dashboard ──
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('auth'))
    return render_template('dashboard.html', username=session['username'])


# ── Error Handlers ──
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return "Internal Server Error", 500


# ── Background Jobs ──
def leaderboard_job():
    """Refresh leaderboards every 30 minutes."""
    while True:
        print("Refreshing leaderboards...")
        refresh_all_leaderboards()
        threading.Event().wait(1800)  # sleep for 30 minutes


if __name__ == '__main__':
    # Register blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_routes)

    # Start Telegram bot polling in background
    threading.Thread(target=run_bot, daemon=True).start()
    # Start leaderboard refresher
    threading.Thread(target=leaderboard_job, daemon=True).start()

    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
