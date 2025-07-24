from flask import Blueprint, request, jsonify
from userdata import (
    get_user,
    save_user_data,
    get_all_users,
    update_user,
    reset_send_limits,
    update_leaderboard_points,
    update_airdrop_requirements,
    update_commissions,
    get_airdrop_requirements,
    get_commission_rates
)

admin_routes = Blueprint('admin_routes', __name__)

@admin_routes.route('/admin/user/balance/set', methods=['POST'])
def set_user_balance():
    data = request.json
    username = data['username']
    balance = float(data['balance'])

    user = get_user(username)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user['wallet'] = balance
    save_user_data(username, user)
    return jsonify({'message': 'Balance updated'})

@admin_routes.route('/admin/user/update_income', methods=['POST'])
def update_user_income():
    data = request.json
    username = data['username']
    income_type = data['type']  # 'referral' or 'task'
    amount = float(data['amount'])

    user = get_user(username)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if income_type == 'referral':
        user['referral_income'] += amount
    elif income_type == 'task':
        user['task_income'] += amount
    else:
        return jsonify({'error': 'Invalid income type'}), 400

    save_user_data(username, user)
    return jsonify({'message': 'Income updated'})

@admin_routes.route('/admin/user/nft', methods=['POST'])
def toggle_nft():
    data = request.json
    username = data['username']
    status = bool(data['status'])

    user = get_user(username)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user['nft_minted'] = status
    save_user_data(username, user)
    return jsonify({'message': 'NFT status updated'})

@admin_routes.route('/admin/user/delete', methods=['POST'])
def delete_user():
    data = request.json
    username = data['username']

    all_users = get_all_users()
    if username not in all_users:
        return jsonify({'error': 'User not found'}), 404

    del all_users[username]
    update_user(all_users)
    return jsonify({'message': 'User deleted'})

@admin_routes.route('/admin/tasks/update', methods=['POST'])
def update_tasks():
    data = request.json
    username = data['username']
    completed_tasks = data['tasks']  # list

    user = get_user(username)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user['tasks_completed'] = len(completed_tasks)
    save_user_data(username, user)
    return jsonify({'message': 'Tasks updated'})

@admin_routes.route('/admin/leaderboard/refresh', methods=['POST'])
def manual_leaderboard_refresh():
    update_leaderboard_points()
    return jsonify({'message': 'Leaderboard refreshed'})

@admin_routes.route('/admin/airdrop/set', methods=['POST'])
def set_airdrop_criteria():
    data = request.json
    update_airdrop_requirements(data)
    return jsonify({'message': 'Airdrop settings updated'})

@admin_routes.route('/admin/airdrop/get')
def get_airdrop_criteria():
    return jsonify(get_airdrop_requirements())

@admin_routes.route('/admin/commissions/set', methods=['POST'])
def set_commissions():
    data = request.json
    update_commissions(data)
    return jsonify({'message': 'Commission rates updated'})

@admin_routes.route('/admin/commissions/get')
def get_commissions():
    return jsonify(get_commission_rates())

@admin_routes.route('/admin/reset_limits', methods=['POST'])
def reset_limits():
    reset_send_limits()
    return jsonify({'message': 'Monthly send/receive limits reset'})
