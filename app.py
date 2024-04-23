from flask import Flask, render_template,request,jsonify,redirect,url_for
from user_handlers import user_handlers
from item_handlers import item_handlers

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.register_blueprint(user_handlers,url_prefix='/user')
app.register_blueprint(item_handlers,url_prefix='/items')

@app.route('/')
def home():
    return render_template('base.html')


if __name__ == '__main__':
    app.run()
