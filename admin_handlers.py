import math

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask import Blueprint
from werkzeug.security import check_password_hash

import RunFirstSettings

admin_handlers = Blueprint('admin_handlers', __name__, static_folder='static', template_folder='templates')

def get_admin_stats():
    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM items')
    total_items = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM transactions')
    total_transactions = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM withdrawRequest')
    total_withdraw_requests = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return {
        'total_users': total_users,
        'total_items': total_items,
        'total_transactions': total_transactions,
        'total_withdraw_requests': total_withdraw_requests
    }


@admin_handlers.route('/home')
def home():
    if 'is_admin' in session and session['is_admin']:
        stats = get_admin_stats()
        return render_template("admin/adminhome.html",stats=stats)
    else:
        return redirect(url_for('home.home'))


@admin_handlers.route('/view_user/<int:user_id>', methods=['GET'])
def view_user(user_id):
    if 'user_id' not in session or not session['is_admin']:
        return redirect(url_for('user_handlers.signin'))

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    # Get user information
    cursor.execute('SELECT user_id,username,email FROM users WHERE user_id = %s', (user_id,))
    user = cursor.fetchone()

    # Get user bids
    cursor.execute('SELECT user_id,item_id,bid_amount,bid_date FROM bids WHERE user_id = %s', (user_id,))
    bids = cursor.fetchall()

    # Get user deposits
    cursor.execute('SELECT deposit_id,deposit_amount,deposit_date FROM deposit WHERE user_id = %s', (user_id,))
    deposits = cursor.fetchall()

    # Get user withdraw requests
    cursor.execute('SELECT withdraw_id,withdraw_amount,withdraw_date,req_state FROM withdrawRequest WHERE user_id = %s', (user_id,))
    withdraw_requests = cursor.fetchall()

    # Get user items
    cursor.execute('SELECT item_id,title,description FROM items WHERE user_id = %s', (user_id,))
    items = cursor.fetchall()

    # Get user transactions
    # NEED UPDATE
    cursor.execute('SELECT item_id,buyer_id,transaction_date FROM transactions WHERE buyer_id = %s', (user_id,))
    transactions = cursor.fetchall()

    conn.close()

    return render_template('admin/admin_view_user.html', user=user, bids=bids, deposits=deposits, withdraw_requests=withdraw_requests, items=items, transactions=transactions)

ITEMS_PER_PAGE = 10

@admin_handlers.route("/view_users/", defaults={'page': 1}, methods=['GET'])
@admin_handlers.route("/view_users/<int:page>", methods=['GET'])
def view_users(page):
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('home.home'))

    search_query = request.args.get('search', '')
    per_page = 10  # Change this as per your requirement
    offset = (page - 1) * per_page

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users WHERE username LIKE %s', ('%' + search_query + '%',))
    total_users = cursor.fetchone()[0]
    total_pages = math.ceil(total_users / per_page)

    if page <= 0 or page > total_pages:
        return render_template('404.html')

    cursor.execute('SELECT user_id,username,email FROM users ORDER BY user_id LIMIT %s OFFSET %s', ( per_page, offset))
    users = cursor.fetchall()

    conn.close()

    return render_template('admin/view_users.html', users=users, search=search_query, total_pages=total_pages+1, current_page=page)

@admin_handlers.route("/view_items/", defaults={'page': 1}, methods=['GET'])
@admin_handlers.route("/view_items/<int:page>", methods=['GET'])
def view_items(page):
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('home.home'))

    search_query = request.args.get('search', '')
    per_page = 10  # Change this as per your requirement
    offset = (page - 1) * per_page

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    # need update on sql query
    cursor.execute('SELECT COUNT(*) FROM items')
    total_users = cursor.fetchone()[0]
    total_pages = math.ceil(total_users / per_page)

    if page <= 0 or page > total_pages:
        return render_template('404.html')

    cursor.execute('SELECT item_id,title,description FROM items  ORDER BY item_id LIMIT %s OFFSET %s', (per_page, offset))
    items = cursor.fetchall()

    conn.close()


    # Update the html!!
    return render_template('admin/view_items.html', items=items , search=search_query, total_pages=total_pages+1, current_page=page)

@admin_handlers.route('/view_transactions', methods=['GET'])
def view_transactions():
    if 'user_id' not in session or not session['is_admin']:
        return redirect(url_for('user_handlers.signin'))

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    # Get all transactions
    cursor.execute('SELECT item_id,buyer_id,transaction_date FROM Transactions ORDER BY transaction_date DESC')
    transactions = cursor.fetchall()

    conn.close()

    return render_template('admin/view_transactions.html', transactions=transactions)

@admin_handlers.route('/view_withdraw_requests')
def view_withdraw_requests():
    if 'user_id' not in session or not session['is_admin']:
        return redirect(url_for('user_handlers.signin'))

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    # Get all withdraw requests
    cursor.execute('SELECT * FROM withdrawrequest ORDER BY withdraw_date DESC')
    requests = cursor.fetchall()
    conn.close()

    return render_template('admin/withdraw_requests.html', requests=requests)

@admin_handlers.route('/accept_withdraw', methods=['POST'])
def accept_withdraw():
    if 'user_id' not in session or not session['is_admin']:
        return redirect(url_for('user_handlers.signin'))

    withdraw_id = request.form['withdraw_id']
    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    # Update the status of the withdraw request in the database
    cursor.execute('UPDATE withdrawrequest SET req_state = %s WHERE withdraw_id = %s', ('Accepted', withdraw_id))
    # Commit the transaction
    conn.commit()
    conn.close()
    # Redirect the user back to the withdraw requests page
    return redirect(url_for('admin_handlers.view_withdraw_requests'))

@admin_handlers.route('/reject_withdraw', methods=['POST'])
def reject_withdraw():
    if 'user_id' not in session or not session['is_admin']:
        return redirect(url_for('user_handlers.signin'))

    withdraw_id = request.form['withdraw_id']

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    cursor.execute('BEGIN')

    # Get the amount and user_id of the withdraw request
    cursor.execute('SELECT user_id, withdraw_amount FROM withdrawrequest WHERE withdraw_id = %s FOR UPDATE', (withdraw_id,))
    user_id, amount = cursor.fetchone()

    cursor.execute('SELECT 1 FROM virtualcurrency WHERE user_id = %s FOR UPDATE', (user_id,))

    # Update the status of the withdraw request in the database
    cursor.execute('UPDATE withdrawrequest SET req_state = %s WHERE withdraw_id = %s', ('Rejected', withdraw_id))

    # Update the user's balance
    cursor.execute('UPDATE virtualcurrency SET balance = balance + %s WHERE user_id = %s', (amount, user_id))

    # Commit the transaction
    conn.commit()
    conn.close()
    # Redirect the user back to the withdraw requests page
    return redirect(url_for('admin_handlers.view_withdraw_requests'))

@admin_handlers.route('/ban_user/<int:user_id>', methods=['GET'])
def ban_user(user_id):
    # UPDATE!! This is just a placeholder

    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('home.home'))

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    cursor.execute('UPDATE users SET is_banned = TRUE WHERE user_id = %s', (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_handlers.view_users'))