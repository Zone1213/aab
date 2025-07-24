from flask import Blueprint, request, jsonify, session
from datetime import datetime
from userdata import (
    get_user,
    create_user,
    save_user_data,
    update_user,
    get_leaderboard_data,
    get_user_position,
    check_airdrop_eligibility
)

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/user/get_dashboard_data')
def get_dashboard_data():
    username = session.get('username')
    user = get_user(username)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    eligibility = check_airdrop_eligibility(username)

    response = {
        "username": username,
        "wallet": user.get("wallet", 0),
        "ref_link": user.get("ref_link", ""),
        "referrals": len(user.get("referrals", [])),
        "referral_income": user.get("referral_income", 0),
        "task_income": user.get("task_income", 0),
        "daily_streak": user.get("daily_streak", 0),
        "tasks_completed": user.get("tasks_completed", 0),
        "nft_minted": user.get("nft_minted", False),
        "airdrop_eligible": eligibility
    }
    return jsonify(response)

@user_bp.route('/user/send', methods=['POST'])
def send():
    data = request.json
    sender = session.get('username')
    receiver = data.get('receiver')
    amount = float(data.get('amount', 0))

    if amount < 1:
        return jsonify({'error': 'Minimum 1 USDT required'}), 400

    sender_user = get_user(sender)
    receiver_user = get_user(receiver)

    if not receiver_user:
        create_user(receiver)
        receiver_user = get_user(receiver)

    send_count = sum(1 for tx in sender_user.get('send_history', []) if tx['to'] == receiver)
    if send_count >= 3:
        return jsonify({'error': 'Max 3 transfers to same user/month'}), 400

    if sender_user['wallet'] < amount:
        return jsonify({'error': 'Insufficient balance'}), 400

    now = datetime.utcnow().isoformat()

    sender_user['wallet'] -= amount
    sender_user['send_history'].append({
        "to": receiver,
        "amount": amount,
        "time": now
    })

    receiver_user['wallet'] += amount
    receiver_user['receive_history'].append({
        "from": sender,
        "amount": amount,
        "time": now
    })

    save_user_data(sender, sender_user)
    save_user_data(receiver, receiver_user)

    return jsonify({'message': 'Transfer successful'})

@user_bp.route('/user/receive')
def receive():
    username = session.get('username')
    user = get_user(username)
    return jsonify({
        "username": username,
        "wallet": user.get("wallet", 0)
    })

@user_bp.route('/user/leaderboard/<category>/<timeframe>')
def leaderboard(category, timeframe):
    board = get_leaderboard_data(category, timeframe)
    username = session.get('username')
    user_pos = get_user_position(category, timeframe, username)

    return jsonify({
        "leaderboard": board[:100],  # Send top 100
        "user": user_pos
    })

@user_bp.route('/user/friend/status/<friend_username>')
def friend_status(friend_username):
    user = get_user(friend_username)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    eligibility = check_airdrop_eligibility(friend_username)

    return jsonify({
        "username": friend_username,
        "wallet": user.get("wallet", 0),
        "referrals": len(user.get("referrals", [])),
        "referral_income": user.get("referral_income", 0),
        "task_income": user.get("task_income", 0),
        "daily_streak": user.get("daily_streak", 0),
        "tasks_completed": user.get("tasks_completed", 0),
        "nft_minted": user.get("nft_minted", False),
        "airdrop_eligible": eligibility
    })
