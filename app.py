from flask import Flask, render_template,request,jsonify,redirect,url_for,session,flash
from flask_socketio import SocketIO

from admin_handlers import admin_handlers
from balance_handlers import balance_handlers
from balance_socket import socketio
from bid_handlers import bid_handlers
from message_routes import message_routes
from user_handlers import user_handlers
from item_handlers import item_handlers
from auction_handlers import auction_handlers
from transaction_handlers import transaction_handlers
from home import home_bp
from errorhandler import error_bp
import barterswap
import RunFirstSettings

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['MAX_CONTENT_LENGTH'] = barterswap.max_content_length
app.secret_key = 'your_secret_key_here'

app.register_blueprint(error_bp)
app.register_blueprint(home_bp, url_prefix='/')
app.register_blueprint(user_handlers,url_prefix='/user')
app.register_blueprint(item_handlers,url_prefix='/items')
app.register_blueprint(bid_handlers, url_prefix='/items/bid')
app.register_blueprint(message_routes, url_prefix='/messages')
app.register_blueprint(admin_handlers, url_prefix='/admin')
app.register_blueprint(auction_handlers, url_prefix="/auctions")
app.register_blueprint(balance_handlers, url_prefix='/balance')
app.register_blueprint(transaction_handlers, url_prefix='/transactions')
socketio.init_app(app)

@app.route('/<path:path>')
def catch_all(path):
    return render_template('404.html'), 404

@app.before_request
def check_ban_status():
    if 'user_id' in session:
        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT is_banned FROM Users WHERE user_id = %s', (session['user_id'],))
        result = cursor.fetchone()
        conn.close()
        if result is not None and result[0]:
            flash("Your account has been banned.", "error")
            return render_template('404.html'), 404

if __name__ == '__main__':
    barterswap.add_bidding_func()
    barterswap.create_scheduler().start()
    barterswap.create_scheduler_transactions().start()
    barterswap.start_database()
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
