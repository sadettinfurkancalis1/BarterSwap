# routes.py
from flask import Flask, render_template, request, redirect, url_for, Blueprint, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os.path
import RunFirstSettings
import uuid
import mimetypes
from PIL import Image
import barterswap

item_handlers = Blueprint('item_handlers', __name__, static_folder='static', template_folder='templates')


@item_handlers.route('/add', methods=['GET', 'POST'])
def add_item():
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))  #

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        category = request.form['category']
        condition = request.form['condition']
        random_filename = None
        try:  # TODO bu try except silinecek
            image = request.files['image']
            if not image:
                raise Exception("No image uploaded!")
            mimetype = mimetypes.guess_type(image.filename)[0]
            if mimetype not in barterswap.ALLOWED_ADDITEM_IMAGE_TYPES:
                return 'Invalid file type', 415
            filename = secure_filename(image.filename)
            random_filename = str(uuid.uuid4()) + os.path.splitext(filename)[1]
            image_path = os.path.join('static/images', random_filename)

            foo = Image.open(image)
            foo = foo.resize((625, 700))
            foo.save(image_path, optimize=True, quality=95)

            print(image, type(image), image_path, random_filename)
        except Exception as e:
            print(e, 12345)
        # ADD FLASH FEATURE IN THE FUTURE
        if len(name) > 100:
            # flash("Item name cannot exceed 100 characters", "error")
            return redirect(url_for('user.add_item'))

        if len(description) > 500:
            # flash("Description cannot exceed 500 characters", "error")
            return redirect(url_for('user.add_item'))

        if len(price) > 10:
            # flash("Price value cannot exceed 10 characters", "error")
            return redirect(url_for('user.add_item'))
        user_id = session['user_id']
        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO items (user_id,title, description, category, starting_price,current_price, condition,image_url) VALUES (%s, %s, %s, %s, %s,%s,%s,%s)',
            (user_id, name, description, category, price, price, condition, random_filename))
        conn.commit()
        conn.close()

        return redirect(url_for('home.home'))  # Ekleme işlemi başarılı olduğunda ana sayfaya yönlendir
    else:
        return render_template('additem.html', max_content_length=barterswap.max_content_length,
                               ALLOWED_IMAGE_TYPES=barterswap.ALLOWED_ADDITEM_IMAGE_TYPES)


@item_handlers.route('/<int:item_id>')
def get_item(item_id):
    # REWRITE WITH BIDS
    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM items WHERE item_id = %s', (item_id,))
    item = list(cursor.fetchone())
    conn.close()
    item[7] = item[7] if item[7] and os.path.exists("static/images/%s" % item[7]) else 'default.png'
    return render_template('item.html', item=tuple(item))


@item_handlers.route('/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id):
    # NEED  update

    if 'user_id' not in session:
        flash("You need to sign in first", "error")

    if request.method == 'POST':
        # check item is owned by session user
        user_id = request.form['user_id']
        if user_id != session['user_id']:
            flash("You can't edit this item", "error")
            return redirect(url_for('home.home'))

        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        condition = request.form['condition']

        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE items SET title = %s, description = %s, category = %s, condition = %s WHERE item_id = %s',
            (name, description, category, condition, item_id))
        conn.commit()
        conn.close()
        item = ()
        return redirect(url_for('item.html', item=item))


@item_handlers.route('/<int:item_id>/bid', methods=['POST'])
def add_bid(item_id):
    # REWRITE
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))

    bid_amount = request.form['bid_amount']

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    # Check if the bid is higher than the current price
    cursor.execute('SELECT current_price FROM items WHERE item_id = %s', (item_id,))
    current_price = cursor.fetchone()[0]
    if bid_amount <= current_price:
        flash("Your bid must be higher than the current price", "error")
        return redirect(url_for('item_handlers.get_item', item_id=item_id))

    # Insert the new bid
    cursor.execute('INSERT INTO bids (user_id, item_id, amount) VALUES (%s, %s, %s)',
                   (session['user_id'], item_id, bid_amount))

    # Update the current price of the item
    cursor.execute('UPDATE items SET current_price = %s WHERE item_id = %s',
                   (bid_amount, item_id))

    conn.commit()
    conn.close()

    return redirect(url_for('item_handlers.get_item', item_id=item_id))
