import json
import os
from datetime import datetime, timedelta

DATA_FILE = 'data.json'
SETTINGS_FILE = 'settings.json'


# --- Core Data Persistence ---

def load_data():
    """Load the entire user database (returns dict of username→user_data)."""
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    """Atomically save the entire user database."""
    tmp_path = DATA_FILE + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(data, f, indent=4)
    os.replace(tmp_path, DATA_FILE)


def load_settings():
    """Load application settings (airdrop requirements & commission rates)."""
    if not os.path.exists(SETTINGS_FILE):
        default = {
            "airdrop_requirements": {
                "min_sends": 120,
                "referral_income": 200,
                "active_referrals": 5,
                "task_earnings": 300,
                "nft_required": True
            },
            "commission_rates": {
                "level1": 10,
                "level2": 5,
                "level3": 2.5
            }
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(default, f, indent=4)
        return default
    with open(SETTINGS_FILE, 'r') as f:
        return json.load(f)

def save_settings(settings):
    """Save application settings."""
    tmp_path = SETTINGS_FILE + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(settings, f, indent=4)
    os.replace(tmp_path, SETTINGS_FILE)


# --- User CRUD Helpers ---

def get_user(username):
    data = load_data()
    return data.get(username)

def create_user(username):
    """Initialize a new user if not exists, with default fields."""
    data = load_data()
    if username not in data:
        data[username] = {
            "username": username,
            "wallet": 0.0,
            "referrals": [],
            "referral_income": 0.0,
            "task_income": 0.0,
            "nft_minted": False,
            "daily_streak": 0,
            "tasks_completed": 0,
            "last_checkin": None,
            "send_history": [],
            "receive_history": [],
            "monthly_send_count": 0,
            "monthly_receive_count": 0,
            "active_refs": [],
            "ref_link": f"https://fahamai.com/referral/{username}"
        }
        save_data(data)
    return data[username]

def save_user_data(username, user_data):
    """Save or overwrite a single user's data."""
    data = load_data()
    data[username] = user_data
    save_data(data)

def get_all_users():
    """Return the full dict of all users."""
    return load_data()

def update_user(all_users_data):
    """Overwrite entire users dict with provided data."""
    save_data(all_users_data)


# --- Admin Utility Functions ---

def reset_send_limits():
    """Reset monthly send/receive counts for all users."""
    data = load_data()
    for user in data.values():
        user['monthly_send_count'] = 0
        user['monthly_receive_count'] = 0
    save_data(data)

def update_leaderboard_points():
    """Recompute and store a 'points' field for each user."""
    data = load_data()
    for user in data.values():
        user['points'] = (
            user.get('referral_income', 0) +
            user.get('task_income', 0) +
            user.get('wallet', 0)
        )
    save_data(data)

def refresh_all_leaderboards():
    """
    Alias for update_leaderboard_points, 
    intended to be called by background job.
    """
    update_leaderboard_points()

def update_airdrop_requirements(new_settings):
    """Overwrite the airdrop_requirements in settings.json."""
    settings = load_settings()
    settings['airdrop_requirements'] = new_settings
    save_settings(settings)

def get_airdrop_requirements():
    """Retrieve current airdrop requirements."""
    return load_settings().get('airdrop_requirements', {})

def update_commissions(new_rates):
    """Overwrite the commission_rates in settings.json."""
    settings = load_settings()
    settings['commission_rates'] = new_rates
    save_settings(settings)

def get_commission_rates():
    """Retrieve current commission rate tiers."""
    return load_settings().get('commission_rates', {})


# --- User‑Facing Helpers ---

def filter_transactions(transactions, timeframe):
    """Filter a list of tx dicts by 'time' field, according to timeframe."""
    now = datetime.utcnow()
    if timeframe == 'today':
        cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif timeframe == 'week':
        cutoff = now - timedelta(days=7)
    elif timeframe == 'month':
        cutoff = now - timedelta(days=30)
    else:
        return transactions
    return [tx for tx in transactions if datetime.fromisoformat(tx['time']) >= cutoff]

def get_leaderboard_data(category, timeframe):
    """Return a sorted list of {username, amount, rank, photo} for the given category."""
    users = get_all_users().values()
    result = []
    for u in users:
        if category == 'top_earners':
            amt = sum(tx['amount'] for tx in filter_transactions(u.get('receive_history', []), timeframe))
        elif category == 'top_senders':
            amt = sum(tx['amount'] for tx in filter_transactions(u.get('send_history', []), timeframe))
        elif category == 'top_referrers':
            amt = len(u.get('referrals', []))
        elif category == 'top_task':
            amt = u.get('tasks_completed', 0)
        else:
            amt = 0
        result.append({
            "username": u.get('username'),
            "amount": round(amt, 2),
            "photo": u.get('photo_url', ''),
        })
    result.sort(key=lambda x: x['amount'], reverse=True)
    for i, entry in enumerate(result, start=1):
        entry['rank'] = i
    return result

def get_user_position(category, timeframe, username):
    """Return the single leaderboard entry for the given user."""
    board = get_leaderboard_data(category, timeframe)
    return next((e for e in board if e['username'] == username), None)


# --- Airdrop Eligibility Check ---

def check_airdrop_eligibility(username):
    user = get_user(username)
    if not user:
        return False
    sends = user.get('send_history', [])
    unique_sends = len({tx['to'] for tx in sends})
    settings = get_airdrop_requirements()
    conditions = [
        unique_sends >= settings.get('min_sends', 0),
        user.get('referral_income', 0) >= settings.get('referral_income', 0),
        len(user.get('active_refs', [])) >= settings.get('active_referrals', 0),
        user.get('task_income', 0) >= settings.get('task_earnings', 0),
        (user.get('nft_minted', False) or not settings.get('nft_required', True))
    ]
    return all(conditions)
